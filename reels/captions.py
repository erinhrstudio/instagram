"""Regole comuni per le didascalie."""
import re

BRAND_TAGS = ["#erinhrstudio", "#1eyedpet"]
MAX_TAGS = 5  # limite di Instagram per post (dicembre 2025): i brand più i primi 3 hashtag del post


def with_brand_tags(caption):
    """Mette #erinhrstudio e #1eyedpet come primi hashtag (senza duplicarli) e tiene al massimo 5 hashtag."""
    for t in BRAND_TAGS:
        caption = re.sub(rf"(?<!\S){re.escape(t)}(?!\w)\s?", "", caption, flags=re.I)
    seen = []

    def keep(m):
        seen.append(m.group(0).lower())
        return m.group(0) if len(seen) <= MAX_TAGS - len(BRAND_TAGS) else ""
    caption = re.sub(r"(?<!\S)#\w+", keep, caption)
    caption = re.sub(r"[ \t]+(?=\n|$)", "", re.sub(r"(?<=\S)[ \t]{2,}", " ", caption)).rstrip()
    first = re.search(r"(?<!\S)#\w", caption)
    tags = " ".join(BRAND_TAGS)
    if first:
        i = first.start()
        return caption[:i] + tags + " " + caption[i:]
    return caption + "\n\n" + tags
