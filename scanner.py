from playwright.async_api import async_playwright
import asyncio
import os
import re
import zipfile

playwright = None
browser = None


# ✅ START BROWSER (ULTRA STABLE)
async def start_browser():
    global playwright, browser

    if browser:
        return browser

    playwright = await async_playwright().start()

    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-infobars"
        ]
    )

    print("✅ TURBO Browser Ready")
    return browser



# ✅ RETRY LOADER (Gov sites fail often)
async def safe_goto(page, url):

    for _ in range(3):  # retry 3 times
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_load_state("networkidle")
            return True
        except:
            await asyncio.sleep(2)

    return False



# ✅ MAIN SCANNER
async def scan_range(bot, browser, chat_id, first, last, district):

    district = district.upper()

    start = int(first)
    end = int(last)

    concurrency = 7   # ⭐ TURBO SPEED
    semaphore = asyncio.Semaphore(concurrency)

    pdf_files = []
    found = 0


    async def process_eld(eld):

        nonlocal found

        async with semaphore:

            page = await browser.new_page()

            try:

                url = f"https://upmines.upsdc.gov.in/Transporter/PrintTransporterFormVehicleCheckValidOrNot.aspx?eId={eld}"

                loaded = await safe_goto(page, url)

                if not loaded:
                    await page.close()
                    return

                await page.emulate_media(media="screen")

                # ⭐ VERY IMPORTANT (fix blank pdf forever)
                await page.wait_for_selector("body")
                await asyncio.sleep(1.5)

                text = await page.inner_text("body")

                if district not in text.upper():
                    await page.close()
                    return


                # ✅ FAST DATA EXTRACT
                def find(pattern):
                    match = re.search(pattern, text, re.I)
                    return match.group(1).strip() if match else "N/A"


                istp = find(r"ISTP\s*No\.?\s*[:\-]?\s*(\d+)")
                ostp = find(r"Transit\s*Pass\s*No\.?\s*[:\-]?\s*(\d+)")
                qty = find(r"(\d+\.?\d*)\s*m3")
                valid = find(r"valid upto\s*[:\-]?\s*([0-9:\-\s]+)")
                generated = find(r"Generated\s*[:\-]?\s*([0-9:/\-\sAPMapm]+)")


                found += 1


                # ⭐ SEND TEXT IMMEDIATELY
                bot.send_message(
                    chat_id,
                    f"""
✅ PERMIT FOUND

📄 ISTP: {istp}
📄 OSTP: {ostp}

⚖ Qty: {qty} m3
📍 District: {district}

⌛ Valid: {valid}
🕒 Generated: {generated}
"""
                )


                # ⭐ PERFECT PDF
                pdf = f"ISTP_{eld}.pdf"

                await page.pdf(
                    path=pdf,
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True
                )

                pdf_files.append(pdf)

            except Exception as e:
                print("SCAN ERROR:", e)

            finally:
                await page.close()



    # ⭐ LIVE START MESSAGE
    bot.send_message(chat_id, "🚀 TURBO Scan Started...\n⚡ Speed Mode Enabled")


    tasks = [process_eld(i) for i in range(start, end + 1)]
    await asyncio.gather(*tasks)



    if found == 0:
        bot.send_message(chat_id, "❌ No permits found.")
        return



    # ⭐ ZIP CREATION
    zip_name = f"Permits_{first}_{last}.zip"

    bot.send_message(chat_id, "📦 Packing permits into ZIP...")

    with zipfile.ZipFile(zip_name, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
        for file in pdf_files:
            zipf.write(file)
            os.remove(file)



    # ⭐ SEND ZIP
    bot.send_message(chat_id, "🚀 Uploading ZIP...")

    with open(zip_name, "rb") as z:
        bot.send_document(chat_id, z)

    os.remove(zip_name)

    bot.send_message(chat_id, f"🔥 TURBO DONE — {found} permits delivered.")
