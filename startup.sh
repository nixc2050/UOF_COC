#!/usr/bin/env bash
set -o errexit
set -o nounset
set -o pipefail

apt-get update
apt-get install -y chromium-browser

# 執行你原本的啟動指令
exec uvicorn UOF_coc_get:app --host=0.0.0.0 --port=10000
