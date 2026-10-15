#!/usr/bin/env python3
"""ママの手帳に届く「Claudeとのやりとり」ダイジェストを暗号化して digest.enc に書き込む。

リポジトリは公開なので、中身は必ず暗号化する（AES-256-GCM）。
鍵はリポジトリに置かない。--key か環境変数 TOKIE_DIGEST_KEY で渡す。

使い方:
  python3 tools/digest.py add  --date 2026-10-15 --file today.txt --key <KEY>
  python3 tools/digest.py show --key <KEY>

digest.enc の形式: base64url( iv(12byte) + 暗号文+タグ ) 、中身は
  {"updated": "...", "days": [{"date": "YYYY-MM-DD", "text": "..."}]}（新しい順）
"""
import argparse, base64, json, os, sys, datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENC = os.path.join(ROOT, "digest.enc")
KEEP_DAYS = 30          # 何日分残すか
MAX_DAY_CHARS = 2500    # 1日分の上限文字数


def b64d(s):
    s = s.strip()
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def b64e(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def load(key):
    if not os.path.exists(ENC):
        return {"updated": None, "days": []}
    raw = b64d(open(ENC, encoding="utf-8").read())
    data = AESGCM(key).decrypt(raw[:12], raw[12:], None)
    return json.loads(data.decode("utf-8"))


def save(key, obj):
    iv = os.urandom(12)
    ct = AESGCM(key).encrypt(iv, json.dumps(obj, ensure_ascii=False).encode("utf-8"), None)
    with open(ENC, "w", encoding="utf-8") as f:
        f.write(b64e(iv + ct))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["add", "show"])
    ap.add_argument("--key", default=os.environ.get("TOKIE_DIGEST_KEY"))
    ap.add_argument("--date")
    ap.add_argument("--file")
    a = ap.parse_args()
    if not a.key:
        sys.exit("鍵がない（--key か TOKIE_DIGEST_KEY）")
    key = b64d(a.key)
    obj = load(key)
    if a.cmd == "show":
        print(json.dumps(obj, ensure_ascii=False, indent=2))
        return
    if not (a.date and a.file):
        sys.exit("add には --date と --file が要る")
    text = open(a.file, encoding="utf-8").read().strip()[:MAX_DAY_CHARS]
    if not text:
        sys.exit("中身が空")
    days = [d for d in obj.get("days", []) if d.get("date") != a.date]
    days.insert(0, {"date": a.date, "text": text})
    days.sort(key=lambda d: d["date"], reverse=True)
    obj = {"updated": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M"),
           "days": days[:KEEP_DAYS]}
    save(key, obj)
    print(f"ok: {a.date} を書き込んだ（全{len(obj['days'])}日分）")


if __name__ == "__main__":
    main()
