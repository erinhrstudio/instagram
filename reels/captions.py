"""Regole comuni per le didascalie."""
import re

BRAND_TAGS = ["#erinhrstudio", "#1eyedpet"]


def with_brand_tags(caption):
    """Mette #erinhrstudio e #1eyedpet come primi hashtag (senza duplicarli)."""
    for t in BRAND_TAGS:
        caption = re.sub(rf"(?<!\S){re.escape(t)}(?!\w)\s?", "", caption, flags=re.I)
    caption = caption.rstrip()
    first = re.search(r"(?<!\S)#\w", caption)
    tags = " ".join(BRAND_TAGS)
    if first:
        i = first.start()
        return caption[:i] + tags + " " + caption[i:]
    return caption + "\n\n" + tags
