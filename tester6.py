#!/usr/bin/env python3
import random
import re                                                     import asyncio                                                import aiohttp                                                import os
import time
import subprocess
import logging                                                from concurrent.futures import ThreadPoolExecutor
                                                              # --- Setup Logging ---
logging.basicConfig(
    filename='whatsapp_tester.log',                               level=logging.DEBUG,                                          format='%(asctime)s - %(levelname)s - %(message)s'        )

# --- Enhanced Config ---
TARGET_REGISTERED = 200                                       HTTP_TIMEOUT = 5
NEGATIVE_REGEX = re.compile(r"Chat on WhatsApp", re.IGNORECASE)
PROFILE_PIC_REGEX = re.compile(r'https://pps\.whatsapp\.net/v/t[^\s"\']+', re.IGNORECASE)                                   H3_REGEX = re.compile(r'<h3[^>]*>([^<]+)</h3>', re.IGNORECASE | re.DOTALL)                                                  IMAGES_DIR = "profile_images"
MAX_CONCURRENT_REQUESTS = 50
BATCH_SIZE = 50
CONNECTION_POOL_SIZE = 100                                    KEEPALIVE_TIMEOUT = 30
HEADERS = {                                                       "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",                                     "Accept-Language": "en-US,en;q=0.5",                          "Accept-Encoding": "gzip, deflate",                           "Connection": "keep-alive",                                   "Upgrade-Insecure-Requests": "1",                             "Cache-Control": "max-age=0",                                 "Referer": "https://web.whatsapp.com/"                    }                                                                                                                           # --- Optimized Utils ---
def sample(arr, n):                                               return random.sample(arr, min(n, len(arr)))                                                                             def insert_at(lst, index, items):                                 return lst[:index] + items + lst[index:]                                                                                # Focused area codes for Pakistan                             AREA_CODES = [                                                    '300', '301', '302', '303', '304', '305', '306', '307', '308', '309',                                                       '310', '311', '312', '313', '314', '315', '316', '317', '318', '319',                                                       '320', '321', '322', '323', '324', '325', '326', '327', '328', '329',                                                       '330', '331', '332', '333', '334', '335', '336', '337', '338', '339',                                                       '340', '341', '342', '343', '344', '345', '346', '347', '348', '349'                                                    ]                                                             DIGITS = list(range(10))                                                                                                    def generate_number():
    code = random.choice(AREA_CODES)                              subscriber = ''.join(str(random.choice(DIGITS)) for _ in range(7))                                                          local = f"0{code}{subscriber}"                                wa_int = f"92{code}{subscriber}"                              wa_link = f"https://api.whatsapp.com/send/?phone={wa_int}&text&type=phone_number&app_absent=0"                              return {"local": local, "waInt": wa_int, "waLink": wa_link}                                                                                                                           UNSAFE_CHARS = re.compile(r'[^A-Za-z0-9_.-]')
def safe_filename_part(s):                                        return UNSAFE_CHARS.sub('_', s.strip())[:200] if s else "no_name"                                                                                                                     # --- Enhanced Async Functions ---                            async def test_number(session, n, semaphore):                     async with semaphore:                                             try:                                                              async with session.get(                                           n["waLink"],                                                  timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT),                                                                          allow_redirects=True                                      ) as res:                                                         if res.status != 200:
                    logging.warning(f"Non-200 status for {n['waLink']}: {res.status}")
                    return None, None, None                                   html = await res.text()                                       if NEGATIVE_REGEX.search(html):
                    return None, None, None                                   profile_pic_match = PROFILE_PIC_REGEX.search(html)                                                                          profile_pic_url = profile_pic_match.group(0) if profile_pic_match else None                                                 h3_matches = H3_REGEX.findall(html)                           h3_text = h3_matches[1].strip() if len(h3_matches) >= 2 else (h3_matches[0].strip() if h3_matches else None)
                if not profile_pic_url:
                    logging.info(f"No profile picture found for {n['waLink']}")                                                             logging.debug(f"Found profile: {n['waLink']} | Pic: {profile_pic_url} | Name: {h3_text}")
                return n, profile_pic_url, h3_text                    except asyncio.TimeoutError:
            logging.error(f"Timeout for {n['waLink']}")                   return None, None, None
        except Exception as e:                                            logging.error(f"Error testing {n['waLink']}: {str(e)}")                                                                     return None, None, None

async def download_profile_picture(session, url, filename):
    try:                                                              clean_url = url.replace("&amp;", "&")                         logging.debug(f"Attempting to download image from {clean_url}")                                                             async with session.get(                                           clean_url,                                                    timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT),            headers=HEADERS                                           ) as pic_res:                                                     if pic_res.status != 200:                                         logging.error(f"Failed to download {clean_url}: Status {pic_res.status}")                                                   return False                                              content = await pic_res.read()                                if len(content) < 100:                                            logging.error(f"Invalid image content for {clean_url} (size: {len(content)} bytes)")                                        return False                                              loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:                            await loop.run_in_executor(executor, _write_file, filename, content)                                                    logging.info(f"Saved image: {filename}")                      return True                                           except Exception as e:
        logging.error(f"Error downloading {clean_url}: {str(e)}")
        return False                                                                                                        def _write_file(filename, content):
    with open(filename, 'wb') as f:                                   f.write(content)

async def upload_to_github(filename):                             try:                                                              subprocess.run(["git", "add", filename], check=True, capture_output=True)
        commit_msg = f"Add new profile image: {os.path.basename(filename)}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)                                        subprocess.run(["git", "push", "origin", "main"], check=True, capture_output=True)                                          print(f"  🚀 Uploaded {filename} to GitHub repo")
        logging.info(f"Uploaded to GitHub: {filename}")               # Delete the image after successful upload
        try:                                                              os.remove(filename)                                           print(f"  🗑️ Deleted local image: {filename}")                 logging.info(f"Deleted local image: {filename}")
        except OSError as e:
            print(f"  ❌ Failed to delete {filename}: {str(e)}")                                                                        logging.error(f"Failed to delete {filename}: {str(e)}")
        return True                                               except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode()
        print(f"  ❌ Git operation failed: {error_msg}")              logging.error(f"Git error for {filename}: {error_msg}")                                                                     return False

async def process_batch_results(results, registered, session):
    for n, profile_pic_url, h3_text in results:                       if n is not None and len(registered) < TARGET_REGISTERED:
            registered.append(n)                                          print(f"{len(registered):02}. Local: {n['local']} | waLink: {n['waLink']}")                                                 logging.info(f"Found: {n['local']} | {n['waLink']}")                                                                        if h3_text:                                                       highlight = f"\033[1;33m{h3_text}\033[0m"                     print(f"  Display name (h3): {highlight}")
            if profile_pic_url:
                name_part = safe_filename_part(h3_text)
                filename = os.path.join(IMAGES_DIR, f"{n['waInt']}_{name_part}.jpg")                                                        success = await download_profile_picture(session, profile_pic_url, filename)                                                if success:
                    print(f"  ✅ Profile picture saved as {filename}")                                                                          await upload_to_github(filename)  # Upload and delete immediately                                                       else:
                    print(f"  ❌ Profile picture download failed for {filename}")
                    logging.error(f"Download failed: {filename}")                                                                       else:
                print(f"  ℹ️ No profile picture available for {n['local']}")
                                                              async def main():
    start_time = time.time()                                      if not os.path.exists(IMAGES_DIR):                                os.makedirs(IMAGES_DIR)                                       print(f"📁 Created directory: {IMAGES_DIR}")
    print(f"🚀 Starting SPEED-OPTIMIZED tester (Target: {TARGET_REGISTERED} numbers)")
    print(f"⚡ Config: {MAX_CONCURRENT_REQUESTS} concurrent, {BATCH_SIZE} batch size, {HTTP_TIMEOUT}s timeout")                 print("-" * 80)
    registered = []
    connector = aiohttp.TCPConnector(
        limit=CONNECTION_POOL_SIZE,                                   limit_per_host=MAX_CONCURRENT_REQUESTS,                       keepalive_timeout=KEEPALIVE_TIMEOUT,                          enable_cleanup_closed=True
    )                                                             semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT, connect=2)
    try:                                                              async with aiohttp.ClientSession(
            connector=connector,                                          headers=HEADERS,
            timeout=timeout
        ) as session:                                                     batch_count = 0                                               while len(registered) < TARGET_REGISTERED:                        batch_count += 1
                batch_start = time.time()                                     batch = [generate_number() for _ in range(BATCH_SIZE)]                                                                      tasks = [test_number(session, n, semaphore) for n in batch]                                                                 results = await asyncio.gather(*tasks, return_exceptions=True)                                                              valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]
                await process_batch_results(valid_results, registered, session)                                                             batch_time = time.time() - batch_start                        found_in_batch = len([r for r in valid_results if r[0] is not None])                                                        print(f"📊 Batch {batch_count}: {found_in_batch}/{BATCH_SIZE} found in {batch_time:.2f}s | Total: {len(registered)}/{TARGET_REGISTERED}")                                                 logging.info(f"Batch {batch_count}: {found_in_batch}/{BATCH_SIZE} found in {batch_time:.2f}s")
                if len(registered) < TARGET_REGISTERED:
                    await asyncio.sleep(0.1)                      except KeyboardInterrupt:                                         print("⚠️ Script interrupted by user. Uploading and deleting any remaining images...")
        logging.info("Script interrupted, checking for images to upload")
        for filename in os.listdir(IMAGES_DIR):                           filepath = os.path.join(IMAGES_DIR, filename)
            if os.path.isfile(filepath):                                      await upload_to_github(filepath)
        print("✅ All available images uploaded and deleted.")    finally:
        total_time = time.time() - start_time
        print("-" * 80)                                               print(f"✅ COMPLETED! Found {len(registered)} registered numbers in {total_time:.2f} seconds")                              print(f"⚡ Average speed: {len(registered)/total_time:.2f} numbers/second")                                                 print(f"🎯 Success rate: {len(registered)}/{batch_count * BATCH_SIZE} = {(len(registered)/(batch_count * BATCH_SIZE))*100:.1f}%")
        logging.info(f"Completed: {len(registered)} numbers in {total_time:.2f}s")
                                                              if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())                                                 asyncio.run(main())
