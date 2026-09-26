"""Sceglie il prossimo episodio, genera il Reel e (se richiesto) lo pubblica.

Uso:
  python -m reels.run                  # prova: genera il video in out/, non pubblica
  python -m reels.run --publish        # genera e pubblica il prossimo episodio
  python -m reels.run --episode riverbero
"""
import argparse, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

from reels.captions import with_brand_tags
from reels.render import EPISODES, render

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "published.json"
OUT = ROOT / "out"


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else []


def next_episode(state):
    done = {s["id"] for s in state}
    todo = [e for e in EPISODES if e["id"] not in done]
    return todo[0] if todo else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--episode")
    a = ap.parse_args()

    state = load_state()
    ep = next(e for e in EPISODES if e["id"] == a.episode) if a.episode else next_episode(state)
    if ep is None:
        print("Tutti gli episodi sono già stati pubblicati: aggiungine altri in reels/episodes.json")
        return 0

    OUT.mkdir(exist_ok=True)
    video = OUT / f"{ep['id']}.mp4"
    render(ep["id"], video)
    (OUT / f"{ep['id']}.txt").write_text(with_brand_tags(ep["caption"]), encoding="utf-8")
    print(f"Generato {video} ({video.stat().st_size // 1024} KB)")

    if not a.publish:
        print("Modalità prova: niente pubblicazione.")
        return 0

    token = os.environ.get("INSTAGRAM_TOKEN")
    if not token:
        print("Manca INSTAGRAM_TOKEN: aggiungilo nei secrets del repository.", file=sys.stderr)
        return 1
    from reels.publish import publish_reel
    res = publish_reel(video, with_brand_tags(ep["caption"]), token)
    state.append({"id": ep["id"], "media_id": res["media_id"],
                  "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    print(f"Pubblicato su @{res['username']}: media {res['media_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
