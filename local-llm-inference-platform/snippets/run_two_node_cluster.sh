#!/usr/bin/env bash
# ------------------------------------------------------------------
# Illustrative demo for this portfolio — NOT the operational script.
# All hosts, IPs, users and paths are placeholders.
# ポートフォリオ用の説明デモです。実運用のスクリプトではありません。
# ホスト・IP・ユーザー・パスはすべてプレースホルダです。
# ------------------------------------------------------------------
#
# 2ノード データ並列レプリカ構成（構成C）の起動デモ:
#   1. 両ノードのモデルが同一であることを検証
#   2. 各ノードで llama-server を起動（ヘッドはローカル、ワーカーはSSH経由）
#   3. nginx LB (:8080) 経由で疎通確認
set -euo pipefail

NODE2="user@203.0.113.11"                       # ワーカーノード（パスワードレスSSH前提）
MODEL="$HOME/models/gguf/example-30b-a3b-q4_k_m.gguf"
PORT=30000
LB_URL="http://127.0.0.1:8080"

# --- 1. モデル整合性チェック（レプリカ構成の前提） ---------------------
local_sum=$(md5sum "$MODEL" | cut -d' ' -f1)
remote_sum=$(ssh "$NODE2" "md5sum '$MODEL' | cut -d' ' -f1")
if [[ "$local_sum" != "$remote_sum" ]]; then
    echo "ERROR: model mismatch between nodes — run rsync first" >&2
    exit 1
fi

# --- 2. 各ノードで llama-server を起動 --------------------------------
start_server() {
    # 共通の起動引数: 全レイヤGPUオフロード・並列スロット・連続バッチング
    echo "llama-server -m '$MODEL' --host 0.0.0.0 --port $PORT \
          -ngl 999 --parallel 16 --ctx-size 32768"
}

echo "[node1] starting llama-server..."
nohup $(start_server) > "$HOME/logs/llama-node1.log" 2>&1 &

echo "[node2] starting llama-server via ssh..."
ssh "$NODE2" "nohup $(start_server) > ~/logs/llama-node2.log 2>&1 &"

# --- 3. LB経由の疎通確認 ----------------------------------------------
echo "waiting for servers to load the model..."
for _ in $(seq 1 60); do
    if curl -sf "$LB_URL/health" > /dev/null; then
        echo "cluster is up: $LB_URL"
        exit 0
    fi
    sleep 5
done

echo "ERROR: cluster did not become healthy in time" >&2
exit 1
