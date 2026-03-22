"""
ag_client.py - GPURental AI Kit クライアントSDK
Usage: python ag_client.py
"""
import urllib.request
import urllib.error
import json
import time

SERVER_URL = "http://localhost:8000"  # ← サーバーIPに変更してください

def send_inference(prompt: str, server_url: str = SERVER_URL) -> dict:
    """推論リクエストを送信する"""
    payload = json.dumps({
        "prompt": prompt,
        "max_tokens": 512,
        "temperature": 0.7
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{server_url}/v1/inference",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": str(e), "status": "failed"}
    except Exception as e:
        return {"error": str(e), "status": "connection_failed"}

def check_health(server_url: str = SERVER_URL) -> dict:
    """サーバーの状態確認"""
    try:
        req = urllib.request.Request(f"{server_url}/health", timeout=5)
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e), "status": "offline"}

def main():
    print("=" * 60)
    print("  GPURental AI Kit - Client Demo")
    print("=" * 60)
    print(f"\n📡 サーバー: {SERVER_URL}")
    print("\n🔍 サーバー状態確認中...")

    health = check_health()
    if "error" in health:
        print(f"❌ サーバーに接続できません: {health['error']}")
        print(f"   → {SERVER_URL} でサーバーが起動しているか確認してください")
        return

    print(f"✅ サーバーオンライン!")
    if "gpu" in health:
        gpu = health["gpu"]
        print(f"   GPU: {gpu.get('name', 'N/A')}")
        print(f"   使用率: {gpu.get('utilization', 'N/A')}")
        print(f"   温度: {gpu.get('temperature', 'N/A')}")

    print("\n" + "=" * 60)
    test_prompts = [
        "AIで動画を自動編集する方法を教えて",
        "RTX A4500でStable Diffusionを動かすには？",
        "GPUレンタルの活用事例を3つ挙げて"
    ]

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📤 テスト {i}: '{prompt}'")
        start = time.time()
        result = send_inference(prompt, SERVER_URL)
        elapsed = time.time() - start

        if result.get("status") == "success":
            print(f"✅ 成功 ({elapsed:.2f}s)")
            print(f"   GPU使用率: {result.get('gpu_utilization', 'N/A')}")
            print(f"   処理時間: {result.get('compute_time_ms', 0)}ms")
            print(f"   応答: {result.get('text', '')[:80]}...")
        else:
            print(f"❌ エラー: {result.get('error', '不明')}")

    print("\n" + "=" * 60)
    print("✅ デモ完了！")

if __name__ == "__main__":
    main()
