// Package gateway — 非同期ジョブAPIゲートウェイの骨子（技術デモ用の匿名サンプル）。
//
// 技術デモ用に書き起こした匿名サンプルであり、実運用コードではない
// (illustrative demo authored for this portfolio; not production source).
//
// 設計意図:
//   - clean architecture: handler は I/O 変換に徹し、業務ロジックは usecase、
//     AWS 依存(DynamoDB/Batch)は repository/client 実装へ隔離する。
//   - 認証は HTTP ミドルウェアに集約し、検証済みの staff_id を context 経由で渡す。
//   - 設定値(テーブル名・ジョブキュー等)は環境変数からのみロードする。
package gateway

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"

	"github.com/go-chi/chi/v5"
	"go.uber.org/zap"
)

// --- context key (staff_id の受け渡し) --------------------------------------

type ctxKey string

const staffIDKey ctxKey = "staff_id"

func staffIDFromContext(ctx context.Context) (string, bool) {
	v, ok := ctx.Value(staffIDKey).(string)
	return v, ok && v != ""
}

// --- 認証ミドルウェア -------------------------------------------------------

// TokenVerifier は Cognito ID トークンを検証し、staff_id クレームを返す。
// 実装側で JWKS のキャッシュ・iss/aud/token_use の検証を行う。
type TokenVerifier interface {
	VerifyAndExtractStaffID(ctx context.Context, rawJWT string) (string, error)
}

// Authenticate は Bearer トークンを検証し、staff_id を context に載せる。
// 失敗時は fail-closed で 401 を返す。
func Authenticate(verifier TokenVerifier, log *zap.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			raw := strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")
			if raw == "" {
				respondError(w, http.StatusUnauthorized, "missing bearer token")
				return
			}

			staffID, err := verifier.VerifyAndExtractStaffID(r.Context(), raw)
			if err != nil {
				log.Warn("jwt verification failed", zap.Error(err))
				respondError(w, http.StatusUnauthorized, "invalid token")
				return
			}

			ctx := context.WithValue(r.Context(), staffIDKey, staffID)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// --- usecase / client の境界 (依存を interface で受ける) ---------------------

type SearchUsecase interface {
	// CreateJob は Batch ジョブを投入し、DynamoDB に投入者スコープで記録する。
	CreateJob(ctx context.Context, staffID string, conditions []Condition) (jobID string, err error)
	// ListJobResult は結果をカーソルページングで返す。
	ListJobResult(ctx context.Context, staffID, jobID string, cursor, limit int) (SheetPage, error)
}

type Condition struct {
	Subject string `json:"subject"`
	Status  string `json:"status"`
	Outline string `json:"outline"`
}

type SheetPage struct {
	Items   []map[string]any `json:"items"`
	HasNext bool             `json:"hasNext"`
	Total   int              `json:"total"`
}

// --- handler (I/O 変換に徹する) ---------------------------------------------

type SearchHandler struct {
	usecase SearchUsecase
	log     *zap.Logger
}

func NewSearchHandler(u SearchUsecase, log *zap.Logger) *SearchHandler {
	return &SearchHandler{usecase: u, log: log}
}

type createJobRequest struct {
	Conditions []Condition `json:"conditions"`
}

type createJobResponse struct {
	JobID string `json:"jobId"`
}

// PostSearchJobs は検索ジョブを投入し、ジョブIDを即返す(submit-then-poll)。
func (h *SearchHandler) PostSearchJobs(w http.ResponseWriter, r *http.Request) {
	staffID, ok := staffIDFromContext(r.Context())
	if !ok {
		respondError(w, http.StatusUnauthorized, "no staff identity")
		return
	}

	var req createJobRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, "invalid body")
		return
	}

	jobID, err := h.usecase.CreateJob(r.Context(), staffID, req.Conditions)
	if err != nil {
		h.log.Error("create job failed", zap.Error(err))
		respondError(w, http.StatusInternalServerError, "failed to create job")
		return
	}

	respondJSON(w, http.StatusOK, createJobResponse{JobID: jobID})
}

// GetSearchJobResult は結果をカーソルページングで返す(投入者スコープ)。
func (h *SearchHandler) GetSearchJobResult(w http.ResponseWriter, r *http.Request) {
	staffID, ok := staffIDFromContext(r.Context())
	if !ok {
		respondError(w, http.StatusUnauthorized, "no staff identity")
		return
	}

	jobID := chi.URLParam(r, "jobID")
	cursor := queryInt(r, "cursor", 0)
	limit := queryInt(r, "limit", 100)

	page, err := h.usecase.ListJobResult(r.Context(), staffID, jobID, cursor, limit)
	if err != nil {
		respondError(w, http.StatusInternalServerError, "failed to fetch result")
		return
	}

	respondJSON(w, http.StatusOK, page)
}

// --- ルーティング(ミドルウェアの積み上げ) -----------------------------------

func NewRouter(h *SearchHandler, verifier TokenVerifier, log *zap.Logger) http.Handler {
	r := chi.NewRouter()
	r.Use(Authenticate(verifier, log))

	r.Route("/v1/search/jobs", func(r chi.Router) {
		r.Post("/", h.PostSearchJobs)
		r.Get("/{jobID}/result", h.GetSearchJobResult)
	})
	return r
}

// --- helpers ----------------------------------------------------------------

func respondJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}

func respondError(w http.ResponseWriter, status int, msg string) {
	respondJSON(w, status, map[string]string{"message": msg})
}

func queryInt(r *http.Request, key string, def int) int {
	// 実際は strconv でパースし、失敗時は def を返す(骨子のため省略)。
	_ = r.URL.Query().Get(key)
	return def
}
