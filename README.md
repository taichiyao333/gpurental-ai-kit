# GPURental AI Kit

GPURental プラットフォーム向けのAI開発キット。GPU提供者が推論APIを簡単に立ち上げ、クライアントがAIリクエストを送れるようにするSDKです。

## 構成

```
gpurental-ai-kit/
├── server/
│   └── ag_server.py   # FastAPI推論サーバー（GPU提供者側）
├── client/
│   └── ag_client.py   # クライアントSDK（利用者側）
└── README.md
```

## クイックスタート

### サーバー側（GPU提供者）

```bash
# 依存関係インストール
pip install fastapi uvicorn pydantic

# サーバー起動
python server/ag_server.py
```

起動後、`http://localhost:8000` で推論APIが利用可能になります。

### クライアント側（利用者）

```bash
# サーバーIPを設定してから実行
python client/ag_client.py
```

## API エンドポイント

| Method | Path | 説明 |
|--------|------|------|
| GET | `/` | サーバー状態確認 |
| GET | `/health` | GPU状態・ヘルスチェック |
| POST | `/v1/inference` | AI推論リクエスト |
| GET | `/v1/models` | 利用可能モデル一覧 |

### 推論リクエスト例

```python
import requests

response = requests.post("http://YOUR_GPU_IP:8000/v1/inference", json={
    "prompt": "AIで動画編集する方法を教えて",
    "max_tokens": 512,
    "temperature": 0.7
})
print(response.json())
```

## GPURental プラットフォームとの統合

このキットは [GPURental](https://gpurental.jp) プラットフォームと連携します。

1. [gpurental.jp/provider](https://gpurental.jp/provider) でGPUを登録
2. エージェント(`gpurental-agent.exe`)をダウンロード・起動
3. このサーバーを起動して推論リクエストを受け付け

## 開発者

METADATALAB.INC — [gpurental.jp](https://gpurental.jp)
