"""Open the deployed app in a headless browser so Streamlit Community Cloud never
puts it to sleep. If it is already asleep, press the wake-up button.
Run by .github/workflows/keepalive.yml every 6 hours."""
import os
import time

from playwright.sync_api import sync_playwright

URL = os.environ.get("APP_URL") or "https://tadawul-app.streamlit.app"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(URL, timeout=120_000)
    time.sleep(15)
    wake = page.get_by_role("button", name="Yes, get this app back up!")
    if wake.count():
        wake.first.click()
        print("App was asleep - wake-up requested")
        time.sleep(90)
    else:
        print("App is awake")
    print("Visited", URL)
    browser.close()
