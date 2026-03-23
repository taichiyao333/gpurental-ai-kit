# -*- coding: utf-8 -*-
"""
GPURental Demo Video Auto-Recorder
=====================================
Run: python demo_recorder.py
Output: demo_output/ folder (.webm video)
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import asyncio
import os
import shutil
from pathlib import Path
from playwright.async_api import async_playwright

# ─── 設定 ───────────────────────────────
OUTPUT_DIR   = Path(__file__).parent / "demo_output"
VIEWPORT     = {"width": 1920, "height": 1080}
MAIN_URL     = "https://gpurental.jp/"
PROVIDER_URL = "https://gpurental.jp/provider/"
DEMO_URL     = "https://inference.gpurental.jp/demo/"

# デモUIのプリセットボタンテキスト (順番に実行)
DEMO_PRESETS = [
    "🚀 GPUレンタルのメリットは？",
    "💰 月収はどれくらい？",
    "⚡ AIアプリを爆速化する方法",
]
# フリー入力の質問
FREE_QUESTION = "AIで動画を自動生成するにはどんなGPUが必要ですか？"

# ─── ユーティリティ ──────────────────────────
async def slow_scroll(page, distance=800, steps=5, delay_ms=200):
    for _ in range(steps):
        await page.mouse.wheel(0, distance // steps)
        await page.wait_for_timeout(delay_ms)

async def slow_scroll_up(page, steps=3):
    for _ in range(steps):
        await page.mouse.wheel(0, -600)
        await page.wait_for_timeout(200)

async def type_slowly(page, selector, text, delay_ms=80):
    """日本語対応のゆっくり入力"""
    loc = page.locator(selector)
    await loc.click()
    await page.wait_for_timeout(300)
    # fill で一度クリア
    await loc.fill("")
    # keyboard.type は Unicode 対応
    await page.keyboard.type(text, delay=delay_ms)

# ─── メイン撮影処理 ────────────────────────────
async def record_demo():
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("🎬 撮影開始...")
    print(f"📁 出力先: {OUTPUT_DIR.absolute()}")

    async with async_playwright() as p:
        # ブラウザ起動（動画録画有効）
        browser = await p.chromium.launch(
            headless=False,  # 実際の画面を表示して録画
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = await browser.new_context(
            viewport=VIEWPORT,
            record_video_dir=str(OUTPUT_DIR),
            record_video_size=VIEWPORT,
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
        )
        page = await context.new_page()

        # ──────────────────────────────────────
        # シーン 1: メインサイト (gpurental.jp)
        # ──────────────────────────────────────
        print("\n📍 シーン1: gpurental.jp")
        await page.goto(MAIN_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)

        # ゆっくりスクロール
        await slow_scroll(page, distance=1200, steps=8, delay_ms=300)
        await page.wait_for_timeout(1500)
        await slow_scroll(page, distance=1200, steps=8, delay_ms=300)
        await page.wait_for_timeout(1500)

        # 上に戻る
        await slow_scroll_up(page, steps=5)
        await page.wait_for_timeout(2000)

        # ──────────────────────────────────────
        # シーン 2: プロバイダーページ
        # ──────────────────────────────────────
        print("📍 シーン2: プロバイダーページ")
        await page.goto(PROVIDER_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        await slow_scroll(page, distance=900, steps=6, delay_ms=350)
        await page.wait_for_timeout(2000)
        await slow_scroll(page, distance=900, steps=6, delay_ms=350)
        await page.wait_for_timeout(2000)

        # ──────────────────────────────────────
        # シーン 3: デモページオープン
        # ──────────────────────────────────────
        print("📍 シーン3: AI デモページ")
        await page.goto(DEMO_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(5000)  # GPU stats 読み込み待ち

        # ヘッダーのGPU情報を見せる（トップで止まる）
        await page.wait_for_timeout(3000)

        # ──────────────────────────────────────
        # シーン 4〜5: プリセット質問を実行
        # ──────────────────────────────────────
        for i, preset_text in enumerate(DEMO_PRESETS, 1):
            print(f"📍 シーン{3+i}: プリセット「{preset_text[:20]}...」")

            # プリセットボタンを探してクリック
            try:
                btn = page.locator(".preset-item").filter(has_text=preset_text.split(" ")[1])
                if await btn.count() == 0:
                    btn = page.locator(".preset-item").nth(i - 1)
                await btn.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                await btn.click()
            except Exception as e:
                print(f"  ⚠️ プリセットボタン: {e} → 入力フォームで代替")
                inp = page.locator("#inp")
                # ラベルテキストからプロンプトを取得
                prompts = [
                    "GPUレンタルサービスを使う主なメリットを3つ、簡潔に日本語で教えてください。",
                    "RTX A4500をGPUレンタルサービスで提供した場合、月にどのくらいの収益が見込めますか？",
                    "PythonのAIアプリケーションをGPUで高速化するための基本的なテクニックを3つ教えてください。",
                ]
                await inp.fill(prompts[i - 1])
                await inp.press("Enter")

            # AI応答を最大60秒待つ
            print("  ⏳ AI応答待ち...")
            try:
                # 「typing」要素が消えるのを待つ
                await page.wait_for_selector("#typing", state="detached", timeout=60000)
            except:
                pass
            await page.wait_for_timeout(5000)  # 回答を読む時間

            # 最後のメッセージまでスクロール
            await page.evaluate("document.getElementById('msgs').scrollTop = 999999")
            await page.wait_for_timeout(3000)

        # ──────────────────────────────────────
        # シーン 6: フリー質問
        # ──────────────────────────────────────
        print(f"Scene6: Free question")
        await type_slowly(page, "#inp", FREE_QUESTION, delay_ms=60)
        await page.wait_for_timeout(800)
        await page.keyboard.press("Enter")

        print("  ⏳ AI応答待ち...")
        try:
            await page.wait_for_selector("#typing", state="detached", timeout=60000)
        except:
            pass
        await page.wait_for_timeout(5000)

        # ──────────────────────────────────────
        # シーン 7: クロージング
        # ──────────────────────────────────────
        print("📍 シーン7: クロージング")
        await page.goto(MAIN_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(4000)

        # 終了
        print("\n✅ 撮影完了！動画を保存中...")
        await context.close()
        await browser.close()

    # 動画ファイルを確認
    videos = list(OUTPUT_DIR.glob("*.webm"))
    if videos:
        latest = max(videos, key=os.path.getmtime)
        size_mb = latest.stat().st_size / 1024 / 1024
        print(f"\n🎬 動画保存完了!")
        print(f"   ファイル: {latest.name}")
        print(f"   サイズ: {size_mb:.1f} MB")
        print(f"   場所: {latest.absolute()}")

        # mp4にリネーム（見やすいように）
        mp4_path = OUTPUT_DIR / "gpurental_ai_demo.webm"
        shutil.copy(latest, mp4_path)
        print(f"\n📁 コピー: {mp4_path.absolute()}")
    else:
        print("⚠️ 動画ファイルが見つかりません")

if __name__ == "__main__":
    asyncio.run(record_demo())
