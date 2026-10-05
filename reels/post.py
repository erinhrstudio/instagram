"""Pubblica un post già pronto (carosello) dalla cartella posts/<nome>/.

La cartella contiene le immagini JPEG (ed eventuali video MP4) in ordine alfabetico e caption.txt.
Le immagini vengono lette da Instagram tramite l'URL pubblico del file su GitHub,
quindi il repository deve essere pubblico.

Uso: python -m reels.post <nome> [--publish | --check] [--reel]
--check crea i contenitori su Instagram senza pubblicare (verifica che accetti immagini e video).
--reel pubblica il post come Reel verticale (media/tiktok/<nome>.mp4, generato se manca).
"""
import argparse, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

from reels.captions import with_brand_tags

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "published.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--reel", action="store_true")
    a = ap.parse_args()
    if a.reel:
        return reel(a)

    folder = ROOT / "posts" / a.name
    images = sorted([*folder.glob("[0-9][0-9]*.jpg"), *folder.glob("[0-9][0-9]*.mp4")], key=lambda p: p.name)
    caption = with_brand_tags((folder / "caption.txt").read_text(encoding="utf-8").strip())
    song = folder / "musica.txt"
    if song.exists():
        print("Canzone consigliata:", song.read_text(encoding="utf-8").strip(),
              "(l'API non permette di aggiungerla: va messa dall'app)")
    if not 2 <= len(images) <= 10:
        print(f"Un carosello richiede da 2 a 10 elementi, trovate {len(images)}", file=sys.stderr)
        return 1
    repo = os.environ.get("GITHUB_REPOSITORY", "erinhrstudio/instagram")
    ref = os.environ.get("GITHUB_SHA", "main")
    def url(p):
        rel = p.relative_to(ROOT).as_posix()
        raw = f"https://raw.githubusercontent.com/{repo}/{ref}/{rel}"
        cdn = f"https://cdn.jsdelivr.net/gh/{repo}@{ref}/{rel}"
        if p.suffix == ".mp4":  # jsDelivr serve i video come video/mp4, GitHub raw no
            return {"video": [cdn, raw]}
        return [raw, cdn]
    urls = [url(p) for p in images]
    print(f"Carosello '{a.name}': {len(urls)} elementi")
    for u in urls:
        print(" ", u)

    if not (a.publish or a.check):
        print("Modalità prova: niente pubblicazione.")
        return 0
    token = os.environ.get("INSTAGRAM_TOKEN")
    if not token:
        print("Manca INSTAGRAM_TOKEN: aggiungilo nei secrets del repository.", file=sys.stderr)
        return 1
    from reels.publish import publish_carousel
    res = publish_carousel(urls, caption, token, publish=a.publish)
    if not a.publish:
        print(f"Verifica riuscita: Instagram accetta tutti gli elementi (contenitore {res['container_id']}, non pubblicato).")
        return 0
    state = json.loads(STATE.read_text()) if STATE.exists() else []
    state.append({"id": f"post:{a.name}", "media_id": res["media_id"],
                  "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    print(f"Pubblicato su @{res['username']}: media {res['media_id']}")
    return 0


def reel(a):
    folder = ROOT / "posts" / a.name
    video = ROOT / "media" / "tiktok" / f"{a.name}.mp4"
    if not video.exists():
        from tools.tiktok_slideshow import render
        render(a.name)
    caption = with_brand_tags((folder / "caption.txt").read_text(encoding="utf-8").strip())
    caption = caption.replace("Nelle slide", "Nel video").replace("nelle slide", "nel video")
    print(f"Reel '{a.name}': {video.relative_to(ROOT)}")
    if not a.publish:
        print("Modalità prova: niente pubblicazione.")
        return 0
    token = os.environ.get("INSTAGRAM_TOKEN")
    if not token:
        print("Manca INSTAGRAM_TOKEN: aggiungilo nei secrets del repository.", file=sys.stderr)
        return 1
    from reels.publish import publish_reel
    res = publish_reel(str(video), caption, token)
    state = json.loads(STATE.read_text()) if STATE.exists() else []
    state.append({"id": f"post:{a.name}", "media_id": res["media_id"], "formato": "reel",
                  "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    print(f"Reel pubblicato su @{res['username']}: media {res['media_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
