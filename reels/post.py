"""Pubblica un post già pronto (carosello) dalla cartella posts/<nome>/.

La cartella contiene le immagini JPEG in ordine alfabetico e caption.txt.
Le immagini vengono lette da Instagram tramite l'URL pubblico del file su GitHub,
quindi il repository deve essere pubblico.

Uso: python -m reels.post <nome> [--publish]
"""
import argparse, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "published.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--publish", action="store_true")
    a = ap.parse_args()

    folder = ROOT / "posts" / a.name
    images = sorted(folder.glob("*.jpg"))
    caption = (folder / "caption.txt").read_text(encoding="utf-8").strip()
    if not 2 <= len(images) <= 10:
        print(f"Un carosello richiede da 2 a 10 immagini, trovate {len(images)}", file=sys.stderr)
        return 1
    repo = os.environ.get("GITHUB_REPOSITORY", "erinhrstudio/instagram")
    ref = os.environ.get("GITHUB_SHA", "main")
    urls = [f"https://raw.githubusercontent.com/{repo}/{ref}/{p.relative_to(ROOT).as_posix()}" for p in images]
    print(f"Carosello '{a.name}': {len(urls)} immagini")
    for u in urls:
        print(" ", u)

    if not a.publish:
        print("Modalità prova: niente pubblicazione.")
        return 0
    token = os.environ.get("INSTAGRAM_TOKEN")
    if not token:
        print("Manca INSTAGRAM_TOKEN: aggiungilo nei secrets del repository.", file=sys.stderr)
        return 1
    from reels.publish import publish_carousel
    res = publish_carousel(urls, caption, token)
    state = json.loads(STATE.read_text()) if STATE.exists() else []
    state.append({"id": f"post:{a.name}", "media_id": res["media_id"],
                  "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    print(f"Pubblicato su @{res['username']}: media {res['media_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
