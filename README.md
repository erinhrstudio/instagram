# Reel automatici — Erin Home Recording Studio

Serie **"Ascolta la differenza"**: Reel verticali da 23 secondi con lo stesso loop prima e dopo un effetto audio (compressione, EQ, riverbero, effetto Haas, saturazione). Gli effetti sono applicati davvero all'audio con FFmpeg; batteria e basso sono sintetizzati. Costo: 0 €.

## Come funziona

- `reels/episodes.json`: gli episodi, con testi, impostazioni dell'effetto e didascalia.
- `reels/render.py`: genera il video 1080x1920.
- `reels/publish.py`: lo carica e lo pubblica con l'API di Instagram.
- `reels/run.py`: sceglie il prossimo episodio non ancora pubblicato (lo stato è in `state/published.json`).
- `.github/workflows/reel.yml`: automazione su GitHub Actions.

## Pubblicazione automatica

L'automazione parte martedì, giovedì e sabato alle 18:30 (ora legale italiana).
Finché la variabile `PUBLISH_ENABLED` non vale `true`, genera solo il video senza pubblicarlo: lo trovi da scaricare nella pagina dell'esecuzione, alla voce Artifacts.

Da impostare in **Settings › Secrets and variables › Actions**:

| Nome | Tipo | A cosa serve |
|---|---|---|
| `INSTAGRAM_TOKEN` | Secret | token dell'app Meta (API con accesso Instagram) |
| `PUBLISH_ENABLED` | Variable | `true` per pubblicare davvero negli orari programmati |
| `GH_PAT` | Secret (facoltativo) | token GitHub con permesso "Secrets: read and write" su questo repository, per rinnovare da solo il token Instagram prima dei 60 giorni |

Per una prova a mano: scheda **Actions › Reel automatico › Run workflow**.

## In locale

```bash
pip install -r requirements.txt
python -m reels.run --episode compressione   # crea out/compressione.mp4
```
