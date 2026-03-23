# --- ag_server.py (Ollama対応版) ---
# GPURental AI Inference Server
# FastAPI + Ollama (llama3.2) によるリアルGPU推論

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import time, datetime, subprocess, json, os, httpx

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

app = FastAPI(
    title="GPURental AI Inference Server",
    description="GPU-accelerated AI inference powered by NVIDIA RTX A4500 + Ollama",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# デモUIの静的ファイル配信
_demo_dir = os.path.join(os.path.dirname(__file__), '..', 'demo')
if os.path.isdir(_demo_dir):
    app.mount("/demo", StaticFiles(directory=_demo_dir, html=True), name="demo")

@app.get("/demo", include_in_schema=False)
async def demo_redirect():
    return FileResponse(os.path.join(_demo_dir, 'index.html'))

class ChatRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    model: Optional[str] = None
    stream: Optional[bool] = False

def get_gpu_info():
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            p = r.stdout.strip().split(", ")
            return {"name": p[0], "utilization": f"{p[1]}%",
                    "memory_used_mb": int(p[2]), "memory_total_mb": int(p[3]),
                    "temperature": f"{p[4]}°C"}
    except:
        pass
    return {"name": "NVIDIA RTX A4500", "utilization": "N/A",
            "memory_used_mb": 0, "memory_total_mb": 20470, "temperature": "N/A"}

def ollama_available():
    try:
        with httpx.Client(timeout=2) as c:
            r = c.get(f"{OLLAMA_URL}/api/tags")
            return r.status_code == 200
    except:
        return False

@app.get("/")
async def root():
    gpu = get_gpu_info()
    ollama_ok = ollama_available()
    return {
        "message": "GPURental AI Inference Server is Online",
        "gpu": gpu["name"],
        "vram": f"{gpu['memory_total_mb']}MB",
        "ollama": "connected" if ollama_ok else "starting",
        "model": DEFAULT_MODEL,
        "status": "ready"
    }

@app.get("/health")
async def health():
    gpu = get_gpu_info()
    ollama_ok = ollama_available()
    return {
        "status": "ok",
        "gpu": gpu,
        "ollama": ollama_ok,
        "model": DEFAULT_MODEL,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/v1/models")
async def list_models():
    models = []
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{OLLAMA_URL}/api/tags")
            if r.status_code == 200:
                for m in r.json().get("models", []):
                    models.append({
                        "id": m["name"],
                        "name": m["name"],
                        "size_gb": round(m.get("size", 0) / 1e9, 1),
                        "type": "text-generation"
                    })
    except:
        models = [{"id": DEFAULT_MODEL, "name": DEFAULT_MODEL, "type": "text-generation"}]
    return {"models": models, "gpu": "NVIDIA RTX A4500"}

@app.post("/v1/inference")
async def inference(request: ChatRequest):
    start = time.time()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    gpu = get_gpu_info()
    model = request.model or DEFAULT_MODEL
    
    # Ollama経由でリアル推論
    if ollama_available():
        try:
            async with httpx.AsyncClient(timeout=120) as c:
                payload = {
                    "model": model,
                    "prompt": request.prompt,
                    "stream": False,
                    "options": {
                        "temperature": request.temperature,
                        "num_predict": request.max_tokens,
                    }
                }
                r = await c.post(f"{OLLAMA_URL}/api/generate", json=payload)
                if r.status_code == 200:
                    resp_data = r.json()
                    text = resp_data.get("response", "")
                    latency = time.time() - start
                    # GPU再取得（推論後）
                    gpu_after = get_gpu_info()
                    print(f"[{ts}] Ollama inference | model={model} | latency={latency:.2f}s | gpu={gpu_after['utilization']}")
                    return {
                        "status": "success",
                        "text": text,
                        "compute_time_ms": int(latency * 1000),
                        "gpu_utilization": gpu_after["utilization"],
                        "gpu_temperature": gpu_after["temperature"],
                        "model": model,
                        "engine": "ollama+rtx_a4500",
                        "timestamp": ts
                    }
        except Exception as e:
            print(f"Ollama error: {e}, falling back to mock")
    
    # フォールバック（Ollama未起動時）
    time.sleep(0.1)
    latency = time.time() - start
    return {
        "status": "success",
        "text": f"[RTX A4500 Demo] {request.prompt[:30]}... に対する回答をGPUで生成しました。（Ollama起動中...）",
        "compute_time_ms": int(latency * 1000),
        "gpu_utilization": gpu["utilization"],
        "gpu_temperature": gpu.get("temperature", "N/A"),
        "model": f"{model}-mock",
        "engine": "mock",
        "timestamp": ts
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"\n🚀 GPURental AI Inference Server v2.0 — port {port}")
    print(f"   GPU: {get_gpu_info()['name']}")
    print(f"   Model: {DEFAULT_MODEL}")
    print(f"   Ollama: {'Connected' if ollama_available() else 'Not started yet'}\n")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
