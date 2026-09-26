"""Coda dei caroselli: sceglie il prossimo post da pubblicare oggi.

state/coda.json contiene l'ordine dei post, la data di inizio e ogni quanti giorni pubblicare.
Stampa il nome del post da pubblicare oggi (o niente) e, su GitHub Actions, lo scrive in GITHUB_OUTPUT.

Uso: python -m reels.coda
"""
import json, os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODA = ROOT / "state" / "coda.json"
STATE = ROOT / "state" / "published.json"


def prossimo(oggi=None):
    oggi = oggi or datetime.now(timezone.utc).date()
    coda = json.loads(CODA.read_text())
    state = json.loads(STATE.read_text()) if STATE.exists() else []
    fatti = {s["id"]: date.fromisoformat(s["published_at"][:10]) for s in state}
    if oggi < date.fromisoformat(coda["inizio"]):
        return None, "la coda parte il " + coda["inizio"]
    date_coda = [fatti[f"post:{n}"] for n in coda["post"] if f"post:{n}" in fatti]
    if date_coda and oggi - max(date_coda) < timedelta(days=coda["ogni_giorni"]):
        return None, f"ultimo post della coda il {max(date_coda)}"
    for n in coda["post"]:
        if f"post:{n}" not in fatti:
            return n, "da pubblicare oggi"
    return None, "coda finita: aggiungi altri post in state/coda.json"


if __name__ == "__main__":
    nome, motivo = prossimo()
    print(nome or "nessun post oggi", "-", motivo)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"name={nome or ''}\n")
