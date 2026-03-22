# --- ag_server.py ---
# GPURental AI Inference Server
# FastAPI-based inference endpoint for GPU providers

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import time
import datetime
import subprocess
import json
import os

app = FastAPI(
    title="GPURental AI Inference Server",
    description="GPU-accelerated AI inference endpoint for the GPURental platform",
    version="1.0.0"
)

# CORS設定（外部クライアントからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── モデル定義 ───────────────────────────────────
class ChatRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    model: Optional[str] = "gpu-default"

class InferenceResponse(BaseModel):
    status: str
    text: str
    compute_time_ms: int
    gpu_utilization: str
    model: str
    timestamp: str

# ── GPU情報取得 ──────────────────────────────────
def get_gpu_info():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            return {
                "name": parts[0],
                "utilization": f"{parts[1]}%",
                "memory_used_mb": int(parts[2]),
                "memory_total_mb": int(parts[3]),
                "temperature": f"{parts[4]}°C"
            }
    except Exception:
        pass
    return {"name": "GPU", "utilization": "N/A", "memory_used_mb": 0, "memory_total_mb": 0, "temperature": "N/A"}

# ── エンドポイント ───────────────────────────────
@app.get("/")
async def root():
    gpu = get_gpu_info()
    return {
        "message": "GPURental AI Inference Server is Online",
        "gpu": gpu["name"],
        "status": "ready"
    }

@app.get("/health")
async def health():
    gpu = get_gpu_info()
    return {
        "status": "ok",
        "gpu": gpu,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.post("/v1/inference", response_model=InferenceResponse)
async def inference(request: ChatRequest):
    start_time = time.time()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # GPU情報を取得
    gpu = get_gpu_info()

    # 推論処理（デモ用モック - 実際のLLM/Stable Diffusionに差し替え可能）
    time.sleep(0.08)  # GPU処理のシミュレーション

    response_text = (
        f"【GPURental GPU Response】\n"
        f"受信時間: {timestamp}\n"
        f"GPU: {gpu['name']} ({gpu['utilization']} 使用中)\n"
        f"解析結果: 『{request.prompt}』を処理しました。\n"
        f"GPUパワーで即座に回答を生成しました。"
    )

    latency = time.time() - start_time

    # ログ出力
    print(f"[{timestamp}] prompt='{request.prompt[:50]}...' | "
          f"latency={latency:.3f}s | gpu={gpu['utilization']}")

    return InferenceResponse(
        status="success",
        text=response_text,
        compute_time_ms=int(latency * 1000),
        gpu_utilization=gpu["utilization"],
        model=request.model,
        timestamp=timestamp
    )

@app.get("/v1/models")
async def list_models():
    return {
        "models": [
            {"id": "gpu-default", "name": "GPURental Default", "type": "text-generation"},
            {"id": "gpu-fast", "name": "GPURental Fast", "type": "text-generation"},
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"\n🚀 GPURental AI Inference Server starting on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
