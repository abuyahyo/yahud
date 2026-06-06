# -*- coding: utf-8 -*-
"""shamela.ws/book/2074 — barcha sahifalarni yuklab pages.json yasaydi."""
import json, os, sys, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

BOOK = 2074
LAST = 8486
OUT_RAW = "raw"            # har sahifa: raw/{N}.html (resume uchun)
OUT_JSON = "pages.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "ar,en;q=0.8"})

os.makedirs(OUT_RAW, exist_ok=True)
lock = threading.Lock()
done = 0

def fetch(n):
    fp = f"{OUT_RAW}/{n}.html"
    if os.path.exists(fp) and os.path.getsize(fp) > 5000:
        return n, True, "cached"
    for attempt in range(4):
        try:
            r = S.get(f"https://shamela.ws/book/{BOOK}/{n}", timeout=30)
            if r.status_code == 200 and len(r.text) > 5000:
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(r.text)
                return n, True, "ok"
            time.sleep(1 + attempt * 2)
        except Exception as e:
            time.sleep(1 + attempt * 2)
            last = str(e)
    return n, False, "fail"

def progress(_):
    global done
    with lock:
        done += 1
        if done % 50 == 0 or done == LAST:
            print(f"  {done}/{LAST}", flush=True)

# 1) yuklab olish (concurrency 6)
pages = list(range(1, LAST + 1))
print(f"fetching {len(pages)} pages …", flush=True)
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = {ex.submit(fetch, n): n for n in pages}
    fails = []
    for f in as_completed(futs):
        n, ok, _ = f.result()
        progress(None)
        if not ok:
            fails.append(n)

if fails:
    print("retrying fails:", len(fails), flush=True)
    for n in fails:
        fetch(n)

# 2) parse → JSON
print("parsing …", flush=True)
items = []
miss = 0
for n in pages:
    fp = f"{OUT_RAW}/{n}.html"
    if not os.path.exists(fp):
        miss += 1; continue
    s = BeautifulSoup(open(fp, encoding="utf-8").read(), "html.parser")
    nass = s.find(class_="nass")
    if not nass:
        miss += 1; continue
    text = nass.get_text("\n", strip=True)
    crumbs = [e.get_text(" ", strip=True) for e in s.find_all(class_="active")]
    crumbs = [c for c in crumbs if c and not c.startswith("رقم")]
    items.append({"p": n, "crumbs": crumbs, "text": text})

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False)

print(f"pages: {len(items)} (miss {miss})  →  {OUT_JSON}", flush=True)
