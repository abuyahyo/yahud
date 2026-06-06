# -*- coding: utf-8 -*-
"""raw/*.html → meta.json + vol-N.json (1..7) + intro.json.

Har bir sahifa: { p: <page>, c: <chapter index in volume>, t: <text> }.
Hajmni kichraytirish uchun jild bo'yicha alohida fayllar; UI faqat ochilgan
jildni yuklaydi. Qidiruv hammasini ketma-ket yuklaydi."""
import os, json, re, sys
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

LAST = 8486
RAW = "raw"

# Jild chegaralari (sahifa kiritsh nuqtalari, s-nav'dan olingan)
VOLUMES = [
    {"n": 0, "title": "المقدمة",                                                "start": 1,    "end": 16,   "file": "intro.json"},
    {"n": 1, "title": "المجلد الأول: الإطار النظرى",                              "start": 17,   "end": 913,  "file": "vol-1.json"},
    {"n": 2, "title": "المجلد الثانى: الجماعات اليهودية.. إشكاليات",              "start": 914,  "end": 2302, "file": "vol-2.json"},
    {"n": 3, "title": "المجلد الثالث: الجماعات اليهودية: التحديث والثقافة",        "start": 2303, "end": 3845, "file": "vol-3.json"},
    {"n": 4, "title": "المجلد الرابع: الجماعات اليهودية.. تواريخ",                 "start": 3846, "end": 5041, "file": "vol-4.json"},
    {"n": 5, "title": "المجلد الخامس: اليهودية.. المفاهيم والفرق",                "start": 5042, "end": 6400, "file": "vol-5.json"},
    {"n": 6, "title": "المجلد السادس: الصهيونية",                                "start": 6401, "end": 7564, "file": "vol-6.json"},
    {"n": 7, "title": "المجلد السابع: إسرائيل.. المستوطن الصهيوني",               "start": 7565, "end": 8486, "file": "vol-7.json"},
]

JUNK_PREFIXES = ("بحث في محتوى", "رقم الجزء", "التشكيل", "المحتوى")

def chapter_of(soup):
    """Joriy bobning sarlavhasi: parent'siz <... class="active"> elementning birinchisi."""
    for e in soup.find_all(class_="active"):
        if not e.parent or not e.parent.get("class"):
            t = e.get_text(" ", strip=True)
            if t and not any(t.startswith(p) for p in JUNK_PREFIXES):
                return t
    return ""

def clean_text(nass):
    # Sahifa raqami yorlig'i (masalan, [الجزء: 5، الصفحة: 123]) odatda kiritilmagan;
    # nass ichidagi havolalar/skript qoldiqlarini olib tashlaymiz.
    for tag in nass.find_all(["script", "style"]):
        tag.decompose()
    t = nass.get_text("\n", strip=True)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t

def parse_page(n):
    fp = f"{RAW}/{n}.html"
    if not os.path.exists(fp):
        return None
    s = BeautifulSoup(open(fp, encoding="utf-8").read(), "html.parser")
    nass = s.find(class_="nass")
    if not nass:
        return None
    return {"chapter": chapter_of(s), "text": clean_text(nass)}

# Har jild uchun: boblar ro'yxati va sahifalar
meta_volumes = []
all_chapters_for_search = []  # global qidiruv uchun

for vol in VOLUMES:
    pages = []
    chapters = []   # [{title, start, end}]
    cur_title = None
    cur_start = None

    for p in range(vol["start"], vol["end"] + 1):
        parsed = parse_page(p)
        if parsed is None:
            continue
        ch_title = parsed["chapter"] or cur_title or vol["title"]
        if ch_title != cur_title:
            if cur_title is not None:
                chapters[-1]["end"] = p - 1
            chapters.append({"title": ch_title, "start": p, "end": p})
            cur_title = ch_title
        else:
            chapters[-1]["end"] = p
        pages.append({"p": p, "c": len(chapters) - 1, "t": parsed["text"]})

    # Jild faylini saqlash
    out = {"volume": vol["n"], "title": vol["title"], "chapters": chapters, "pages": pages}
    with open(vol["file"], "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)

    meta_volumes.append({
        "n": vol["n"], "title": vol["title"],
        "start": vol["start"], "end": vol["end"],
        "file": vol["file"],
        "pageCount": len(pages),
        "chapterCount": len(chapters),
    })
    print(f"vol {vol['n']:>1}: pages={len(pages):>4}  chapters={len(chapters):>3}  → {vol['file']}")

meta = {
    "title": "موسوعة اليهود واليهودية والصهيونية",
    "author": "د. عبد الوهاب المسيري",
    "source": "https://shamela.ws/book/2074",
    "totalPages": LAST,
    "volumes": meta_volumes,
}
with open("meta.json", "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=1)
print("→ meta.json")
