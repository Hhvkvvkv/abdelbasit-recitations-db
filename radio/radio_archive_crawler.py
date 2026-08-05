#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
زاحف أرشيف برنامج «تلاوت قاری مصری - عبدالباسط محمد عبدالصمد» على راديو تلاوت
(radio.iranseda.ir — program m=165100)

- يعمل مباشرة بدون بروكسي — شغّله على سيرفر الإنترنت العادي
- يجلب كل الحلقات (آلاف الحلقات اليومية) مع روابط التحميل المباشرة لكل حلقة
  (كل حلقة = مقطعان، كل مقطع متاح على سيرفرين 8 و 12)

الاستخدام:
    python3 radio_archive_crawler.py            # كل الصفحات
    python3 radio_archive_crawler.py --max-pages 3   # آخر 60 حلقة فقط
"""
import argparse, html, json, re, sys, time
from urllib.parse import quote

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "requests"])
    import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"}
BASE = "http://radio.iranseda.ir"
PROG = 165100

def get(url, retries=4):
    for i in range(retries):
        try:
            r = requests.get(url, headers=UA, timeout=60)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"[!] retry {url}: {e}", file=sys.stderr)
            time.sleep(4 * (i + 1))
    return ""

def parse_episodes(text):
    items = []
    for m in re.finditer(r'epgarchivePart/\?VALID=TRUE&ch=28&e=(\d+)', text):
        seg = text[m.start():m.start() + 3000]
        d = re.search(r'<h2>([^<]*)</h2>', seg)
        mo = re.search(r'<h4>([^<]*)<span[^>]*>([^<]*)</span>', seg)
        t = re.search(r'ott-name[^>]*>\s*([^<]+?)\s*</p>', seg)
        date = f"{d.group(1).strip()} {mo.group(1).strip()} {mo.group(2).strip()}" if d and mo else ""
        items.append({"e": m.group(1), "title": html.unescape(t.group(1)).strip() if t else "",
                      "date": date.replace("\u0660", "0").replace("\u0661", "1").replace("\u0662", "2")
                                       .replace("\u0663", "3").replace("\u0664", "4").replace("\u0665", "5")
                                       .replace("\u0666", "6").replace("\u0667", "7").replace("\u0668", "8")
                                       .replace("\u0669", "9")})
    seen, out = set(), []
    for it in items:
        if it["e"] not in seen:
            seen.add(it["e"]); out.append(it)
    return out

def parse_episode_links(text):
    links = []
    for m in re.finditer(r'headend2\.iranseda\.ir/DLFile/\?VALID=TRUE&amp;vid=(\d+_\d+)', text):
        links.append(f"https://headend2.iranseda.ir/DLFile/?VALID=TRUE&vid={m.group(1)}")
    seen = []
    for l in links:
        if l not in seen:
            seen.append(l)
    return seen

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=0)
    ap.add_argument("--out", default="radio_archive_abdelbasit.json")
    args = ap.parse_args()

    episodes = []
    pn = 1
    while True:
        txt = get(f"{BASE}/Program/?ch=28&m={PROG}&pn={pn}")
        items = parse_episodes(txt)
        if not items:
            break
        print(f"[*] page {pn}: {len(items)} episodes", file=sys.stderr)
        episodes.extend(items)
        if args.max_pages and pn >= args.max_pages:
            break
        pn += 1
        time.sleep(1)

    print(f"[*] total episodes: {len(episodes)} — now fetching each episode links ...", file=sys.stderr)
    for i, ep in enumerate(episodes, 1):
        txt = get(f"{BASE}/epgarchivePart/?VALID=TRUE&ch=28&e={ep['e']}")
        ep["links"] = parse_episode_links(txt)
        if i % 20 == 0:
            print(f"[*] {i}/{len(episodes)}", file=sys.stderr)
            json.dump(episodes, open(args.out, "w", encoding="utf-8"), ensure_ascii=False)
        time.sleep(1.5)

    json.dump(episodes, open(args.out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"[+] saved -> {args.out}")

if __name__ == "__main__":
    main()
