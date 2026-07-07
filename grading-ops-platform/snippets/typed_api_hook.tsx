// 型付きReactデータフック＋環境変数設定（技術デモ用の匿名サンプル）。
//
// 技術デモ用に書き起こした匿名サンプルであり、実運用コードではない
// (illustrative demo authored for this portfolio; not production source).
//
// 設計意図:
//   - APIエンドポイントは環境別設定に集約し、コード中にURLを直書きしない。
//   - CognitoのIDトークンを毎リクエストに載せる薄い型付きクライアント層。
//   - ブラウザに一時保持する機密値はAES暗号化し、暗号鍵は環境変数から解決する
//     （鍵をソースへ直書きしない）。

import { fetchAuthSession } from "aws-amplify/auth";
import axios, { AxiosInstance } from "axios";
import CryptoJS from "crypto-js";
import { useCallback, useEffect, useState } from "react";

// --- 環境別設定（dev/stg/prod をビルド時env varで切替） ---------------------

type ApiConfig = {
  adpalBaseUrl: string;
};

const config: ApiConfig = {
  // 例: https://<api-id>.execute-api.<region>.amazonaws.com
  adpalBaseUrl: process.env.NEXT_PUBLIC_ADPAL_BASE_URL ?? "",
};

// --- 型定義（バックエンドのOpenAPI型と対応させる） --------------------------

export type SearchSheet = {
  answerSheetId: string;
  examinerName: string;
  status: string;
  scheduledReturnDate: string | null;
};

export type SearchJobResult = {
  items: SearchSheet[];
  hasNext: boolean;
  total: number;
};

// --- 認証付きクライアント生成 -----------------------------------------------

async function createClient(baseURL: string): Promise<AxiosInstance> {
  const session = await fetchAuthSession();
  const idToken = session.tokens?.idToken?.toString() ?? "";

  return axios.create({
    baseURL,
    headers: { Authorization: `Bearer ${idToken}` },
    timeout: 15_000,
  });
}

// --- 型付きデータフック（submit-then-poll の結果取得側） ---------------------

type UseSearchResult = {
  data: SearchJobResult | null;
  loading: boolean;
  error: Error | null;
  reload: () => void;
};

export function useSearchJobResult(
  jobId: string,
  cursor = 0,
  limit = 100,
): UseSearchResult {
  const [data, setData] = useState<SearchJobResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const client = await createClient(config.adpalBaseUrl);
      const res = await client.get<SearchJobResult>(
        `/v1/search/jobs/${jobId}/result`,
        { params: { cursor, limit } },
      );
      setData(res.data);
    } catch (e) {
      setError(e instanceof Error ? e : new Error("unknown error"));
    } finally {
      setLoading(false);
    }
  }, [jobId, cursor, limit]);

  useEffect(() => {
    if (jobId) void load();
  }, [jobId, load]);

  return { data, loading, error, reload: load };
}

// --- 機密値のAES暗号化ストレージ（鍵は環境変数から解決） --------------------

const STORAGE_SECRET = process.env.NEXT_PUBLIC_STORAGE_SECRET ?? "";

export function setSecretItem(key: string, value: string): void {
  if (!STORAGE_SECRET) throw new Error("storage secret is not configured");
  const encrypted = CryptoJS.AES.encrypt(value, STORAGE_SECRET).toString();
  localStorage.setItem(key, encrypted);
}

export function getSecretItem(key: string): string {
  const raw = localStorage.getItem(key);
  if (!raw || !STORAGE_SECRET) return "";
  const bytes = CryptoJS.AES.decrypt(raw, STORAGE_SECRET);
  return bytes.toString(CryptoJS.enc.Utf8);
}
