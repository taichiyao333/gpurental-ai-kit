# -*- coding: utf-8 -*-
"""
GPURental Multi-Video Recorder
================================
Video 2: CPU vs GPU Speed Comparison
Video 3: Cost Comparison  
Video 4: Provider Registration
Run: python multi_recorder.py
"""
import sys, io, asyncio, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR   = Path(__file__).parent / "demo_output"
VIEWPORT     = {"width": 1920, "height": 1080}
COMPARE_URL  = "https://inference.gpurental.jp/demo/compare.html"
MAIN_URL     = "https://gpurental.jp/"
PROVIDER_URL = "https://gpurental.jp/provider/"
DEMO_URL     = "https://inference.gpurental.jp/demo/"

async def scroll(page, dist=800, steps=6, ms=280):
    for _ in range(steps):
        await page.mouse.wheel(0, dist // steps)
        await page.wait_for_timeout(ms)

async def scroll_up(page, steps=4):
    for _ in range(steps):
        await page.mouse.wheel(0, -500)
        await page.wait_for_timeout(220)

async def make_context(p, video_name):
    OUTPUT_DIR.mkdir(exist_ok=True)
    browser = await p.chromium.launch(
        headless=False,
        args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
    )
    ctx = await browser.new_context(
        viewport=VIEWPORT,
        record_video_dir=str(OUTPUT_DIR),
        record_video_size=VIEWPORT,
        locale="ja-JP",
        timezone_id="Asia/Tokyo",
    )
    return browser, ctx

async def save_video(ctx, browser, name):
    await ctx.close()
    await browser.close()
    videos = sorted(OUTPUT_DIR.glob("*.webm"), key=os.path.getmtime, reverse=True)
    if videos:
        dest = OUTPUT_DIR / f"{name}.webm"
        shutil.copy(videos[0], dest)
        size = dest.stat().st_size / 1024 / 1024
        print(f"  Saved: {dest.name} ({size:.1f} MB)")
    await asyncio.sleep(1)

# ═══════════════════════════════════════════════
# VIDEO 2: CPU vs GPU Speed Comparison
# ═══════════════════════════════════════════════
async def record_video2(p):
    print("\n[VIDEO 2] CPU vs GPU Speed Comparison")
    browser, ctx = await make_context(p, "video2")
    page = await ctx.new_page()

    # Open compare page
    print("  Opening compare page...")
    await page.goto(COMPARE_URL, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(4000)

    # Show the page layout briefly
    await page.wait_for_timeout(2000)

    # Click "比較スタート"
    print("  Clicking start button...")
    start_btn = page.locator("#startBtn")
    await start_btn.scroll_into_view_if_needed()
    await page.wait_for_timeout(1000)
    await start_btn.click()

    # Wait for both results (CPU ~30s + GPU ~10s => wait up to 90s)
    print("  Waiting for CPU + GPU results (up to 90s)...")
    try:
        await page.wait_for_selector(".result-banner.show", timeout=90000)
        print("  Results appeared!")
    except:
        print("  Timeout, continuing...")

    # Show result for 8 seconds
    await page.wait_for_timeout(8000)

    # Scroll to result banner
    await page.evaluate("document.getElementById('resultBanner').scrollIntoView({behavior:'smooth'})")
    await page.wait_for_timeout(5000)

    # CTA
    await page.evaluate("document.querySelector('.cta-btn').scrollIntoView({behavior:'smooth'})")
    await page.wait_for_timeout(4000)

    print("  Saving video 2...")
    await save_video(ctx, browser, "video2_cpu_vs_gpu")


# ═══════════════════════════════════════════════
# VIDEO 3: Cost Comparison Page
# ═══════════════════════════════════════════════
async def record_video3(p):
    print("\n[VIDEO 3] Cost Comparison")
    browser, ctx = await make_context(p, "video3")
    page = await ctx.new_page()

    # Open cost compare page
    await page.goto(COMPARE_URL.replace("compare.html", "cost.html"), wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(3000)
    await scroll(page, dist=1200, steps=8, ms=320)
    await page.wait_for_timeout(3000)
    await scroll(page, dist=800, steps=6, ms=320)
    await page.wait_for_timeout(3000)

    await page.goto(PROVIDER_URL, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(3000)
    await scroll(page, dist=1000, steps=7, ms=300)
    await page.wait_for_timeout(4000)

    print("  Saving video 3...")
    await save_video(ctx, browser, "video3_cost_comparison")


# ═══════════════════════════════════════════════
# VIDEO 4: Agent Setup (Provider Registration)
# ═══════════════════════════════════════════════
async def record_video4(p):
    print("\n[VIDEO 4] Provider Agent Registration")
    browser, ctx = await make_context(p, "video4")
    page = await ctx.new_page()

    # Top page
    await page.goto(MAIN_URL, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(3000)
    await scroll(page, dist=600, steps=5, ms=250)
    await page.wait_for_timeout(2000)

    # Provider page
    await page.goto(PROVIDER_URL, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(4000)
    await scroll(page, dist=800, steps=6, ms=300)
    await page.wait_for_timeout(3000)

    # Highlight download section if visible
    try:
        dl_area = page.locator(".agent-install, [id*='download'], [class*='download']").first
        if await dl_area.count() > 0:
            await dl_area.scroll_into_view_if_needed()
            await page.wait_for_timeout(4000)
    except:
        pass

    await scroll(page, dist=600, steps=5, ms=300)
    await page.wait_for_timeout(4000)

    await page.goto(DEMO_URL, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(5000)

    # One demo question
    btn = page.locator(".preset-item").first
    if await btn.count() > 0:
        await btn.click()
        try:
            await page.wait_for_selector("#typing", state="detached", timeout=45000)
        except:
            pass
        await page.wait_for_timeout(5000)

    print("  Saving video 4...")
    await save_video(ctx, browser, "video4_provider_setup")


# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════
async def main():
    print("=== GPURental Multi-Video Recorder ===")
    print(f"Output: {OUTPUT_DIR.absolute()}")

    async with async_playwright() as p:
        await record_video2(p)
        await asyncio.sleep(3)
        await record_video4(p)

    # List results
    print("\n=== DONE ===")
    for v in sorted(OUTPUT_DIR.glob("video*.webm"), key=os.path.getmtime):
        size = v.stat().st_size / 1024 / 1024
        print(f"  {v.name}: {size:.1f} MB")

if __name__ == "__main__":
    asyncio.run(main())
