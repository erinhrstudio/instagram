"""Piano delle uscite su YouTube Shorts (dal 24/10/2026).

Su YouTube vanno i Reel con il loro audio (gli esperimenti di psicoacustica): i caroselli
diventerebbero video muti. I video si caricano privati con l'ora di uscita programmata
(status.publishAt): li carica la routine del mattino via Composio, perché la quota di
caricamenti condivisa si azzera alle 9 italiane.

state/youtube.json: un elemento per video con file, titolo, descrizione, tag, uscita (ora di Roma),
video_id (vuoto finché non è caricato).

Uso: python -m tools.youtube_piano            # stampa il piano
     python -m tools.youtube_piano --scrivi   # aggiunge al file i video che mancano
"""
import json, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "state" / "youtube.json"
ROMA = ZoneInfo("Europe/Rome")
TAGS = ["#erinhrstudio", "#1eyedpet", "#shorts", "#psicoacustica", "#illusioniuditive"]

# Reel nuovi: stessa data e ora di Instagram (calendario della coda al 24/10).
NUOVI = [("fischio-silenzio", "2026-10-27 18:00"), ("rumore-nota", "2026-10-30 12:00"),
         ("battito-binaurale", "2026-11-02 18:00"), ("scale-zigzag", "2026-11-05 12:00"),
         ("galoppo", "2026-11-07 12:00")]
# Reel già usciti su Instagram: uno al giorno alle 15:00, dai più forti.
ARCHIVIO = ["beat-infinito", "buchi", "scala-infinita", "parole-fantasma", "haas", "piu-forte",
            "tritono", "fischi-parole", "mascheramento", "ottava", "melodia-nascosta", "parlato-canto"]


def testi(nome):
    righe = (ROOT / "posts" / nome / "reel_caption.txt").read_text(encoding="utf-8").strip().split("\n\n")
    corpo = [p for p in righe if not p.startswith("#")]
    titolo = corpo[0].split("\n")[0].strip()
    if len(titolo) > 90:
        titolo = titolo[:87].rsplit(" ", 1)[0] + "…"
    descr = "\n\n".join(corpo[1:])
    descr = descr.replace("nelle slide", "nel video").replace("dopo le slide", "dopo il video")
    descr += "\n\nIscriviti: ogni settimana una nuova illusione dell'udito 🎧\n\n" + " ".join(TAGS)
    return titolo + " #shorts", descr


def piano():
    out = []
    for nome, quando in NUOVI:
        out.append((nome, f"media/youtube/{nome}.mp4", quando))
    for i, nome in enumerate(ARCHIVIO):
        out.append((nome, f"media/tiktok/{nome}.mp4", f"2026-10-{25 + i:02d} 15:00" if 25 + i <= 31
                    else f"2026-11-{25 + i - 31:02d} 15:00"))
    return out


def main():
    stato = json.loads(FILE.read_text()) if FILE.exists() else []
    noti = {s["nome"] for s in stato}
    for nome, f, quando in piano():
        titolo, descr = testi(nome)
        utc = datetime.strptime(quando, "%Y-%m-%d %H:%M").replace(tzinfo=ROMA).astimezone(ZoneInfo("UTC"))
        item = {"nome": nome, "file": f, "titolo": titolo, "descrizione": descr,
                "tag": ["psicoacustica", "illusioni uditive", "auditory illusion", "home recording", "erinhrstudio"],
                "uscita_roma": quando, "publish_at": utc.strftime("%Y-%m-%dT%H:%M:%SZ"), "video_id": ""}
        print(f"{quando}  {nome:18s} {titolo}")
        if nome not in noti:
            stato.append(item)
    if "--scrivi" in sys.argv:
        stato.sort(key=lambda s: s["publish_at"])
        FILE.write_text(json.dumps(stato, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
