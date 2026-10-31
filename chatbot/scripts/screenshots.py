"""End-to-end UI check + README screenshots (Playwright/Chromium, demo mode).

    LLM_PROVIDER=fake uvicorn secim_chatbot.web.app:app --port 8765 &
    python scripts/screenshots.py --url http://127.0.0.1:8765
"""
import argparse
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"


def ask(page, question, n):
    page.fill("#q", question)
    page.keyboard.press("Enter")
    expect(page.locator("article.msg.bot").nth(n)).not_to_have_text("Sorgu yazılıyor", timeout=15000)
    page.wait_for_function(f"document.querySelectorAll('article.msg.bot .answer').length > {n}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8765")
    a = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # 1) desktop, light: landing page with example chips
        page = browser.new_page(viewport={"width": 1280, "height": 860}, device_scale_factor=2)
        page.on("console", lambda m: m.type == "error" and errors.append(m.text))
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(a.url)
        expect(page.locator(".chip").first).to_be_visible()
        expect(page.locator("#status-text")).to_have_text("demo modu")
        page.screenshot(path=OUT / "01-baslangic.png")

        # 2) click an example chip, then type a follow-up; open the SQL of the second answer
        page.locator(".chip", has_text="2017 anayasa referandumunda").click()
        page.wait_for_selector("article.msg.bot .answer")
        expect(page.locator("article.msg.bot table tbody tr")).to_have_count(5)
        ask(page, "2024 yerel seçimlerinde İstanbul'un 39 ilçesinden kaçını hangi parti kazandı?", 1)
        page.locator("article.msg.bot").nth(1).locator("summary").click()
        expect(page.locator("article.msg.bot").nth(1).locator("pre")).to_contain_text("2024yerel")
        page.set_viewport_size({"width": 1280, "height": 1250})
        page.wait_for_timeout(600)
        page.screenshot(path=OUT / "02-sohbet.png")

        # 3) a refusal (demo mode knows only verified questions)
        ask(page, "Yarın İstanbul'da hava nasıl olacak?", 2)
        expect(page.locator("article.msg.bot.refused")).to_have_count(1)
        page.close()

        # 4) mobile, dark mode, time series with bars and the SQL open
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3,
                                  color_scheme="dark", is_mobile=True, has_touch=True)
        m = ctx.new_page()
        m.on("pageerror", lambda e: errors.append(str(e)))
        m.goto(a.url)
        m.wait_for_selector(".chip")
        m.evaluate("window.secimAsk(\"2002'den bu yana genel seçimlerde AK Parti'nin İstanbul'daki oy oranı nasıl değişti?\")")
        m.wait_for_selector("article.msg.bot .answer")
        expect(m.locator("article.msg.bot table tbody tr")).to_have_count(7)
        m.locator("article.msg.bot summary").click()
        overflow = m.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        assert not overflow, "yatay taşma var (mobil)"
        m.wait_for_timeout(600)
        m.screenshot(path=OUT / "03-mobil-karanlik.png")

        # 5) desktop: mahalle-level question
        page = browser.new_page(viewport={"width": 1280, "height": 760}, device_scale_factor=2)
        page.goto(a.url)
        page.locator(".chip", has_text="Ümraniye").click()
        page.wait_for_selector("article.msg.bot .answer")
        page.locator("article.msg.bot summary").click()
        page.wait_for_timeout(600)
        page.screenshot(path=OUT / "04-mahalle.png")
        browser.close()

    assert not errors, errors
    print("UI uçtan uca kontrol tamam; ekran görüntüleri:", *sorted(str(p) for p in OUT.glob("*.png")), sep="\n  ")


if __name__ == "__main__":
    main()
