"""Statistiche dei post Instagram: copertura, visualizzazioni, salvataggi, condivisioni per formato.

Uso (su GitHub Actions, con INSTAGRAM_TOKEN): python -m tools.stats
"""
import os
from collections import defaultdict

import requests

API = "https://graph.instagram.com/v23.0"
TOK = os.environ["INSTAGRAM_TOKEN"]
METRICS = ["reach", "views", "saved", "shares", "total_interactions"]


def get(path, **params):
    r = requests.get(f"{API}/{path}", params={"access_token": TOK, **params}, timeout=30).json()
    return r


def insights(mid):
    out = {}
    for m in METRICS:  # una per volta: se una metrica non vale per quel formato, le altre restano
        r = get(f"{mid}/insights", metric=m)
        for d in r.get("data", []):
            out[d["name"]] = d["values"][0]["value"] if d.get("values") else d.get("total_value", {}).get("value")
    return out


def main():
    media, url = [], "me/media"
    params = dict(fields="id,caption,media_type,media_product_type,timestamp,like_count,comments_count", limit=100)
    r = get(url, **params)
    media += r.get("data", [])
    rows = []
    for m in media:
        fmt = "REEL" if m.get("media_product_type") == "REELS" else m["media_type"]
        ins = insights(m["id"])
        cap = (m.get("caption") or "").split("\n")[0][:45].replace("|", "/")
        rows.append((m["timestamp"][:10], fmt, ins.get("views"), ins.get("reach"), ins.get("saved"),
                     ins.get("shares"), m.get("like_count"), m.get("comments_count"), cap))
    print("| data | formato | views | reach | salvati | condivisioni | like | commenti | post |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join("" if v is None else str(v) for v in r) + " |")
    agg = defaultdict(list)
    for r in rows:
        agg[r[1]].append(r)
    print("\nMEDIE PER FORMATO")
    for fmt, rs in agg.items():
        def avg(i):
            v = [x[i] for x in rs if isinstance(x[i], (int, float))]
            return round(sum(v) / len(v), 1) if v else "-"
        print(f"{fmt}: n={len(rs)} views={avg(2)} reach={avg(3)} salvati={avg(4)} condivisioni={avg(5)} like={avg(6)}")


if __name__ == "__main__":
    main()
