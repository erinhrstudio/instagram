"""Regole comuni per le didascalie."""
import re

BRAND_TAGS = ["#erinhrstudio", "#1eyedpet"]
MAX_TAGS = 5  # limite di Instagram per post (dicembre 2025): i brand più i primi 3 hashtag del post


# Dall'8/11 niente emoji (Giuseppe le odia; i dati non mostrano vantaggi, semmai il contrario).
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D\u20E3]")


def no_emoji(text):
    """Toglie le emoji e gli spazi che restano appesi."""
    text = EMOJI.sub("", text)
    return re.sub(r"[ \t]+(?=\n|$)", "", re.sub(r"(?<=\S)[ \t]{2,}", " ", text))


def with_brand_tags(caption):
    caption = no_emoji(caption)
    """Mette #erinhrstudio e #1eyedpet come primi hashtag (senza duplicarli) e tiene al massimo 5 hashtag."""
    for t in BRAND_TAGS:
        caption = re.sub(rf"(?<!\S){re.escape(t)}(?!\w)\s?", "", caption, flags=re.I)
    seen = []

    def keep(m):
        seen.append(m.group(0).lower())
        return m.group(0) if len(seen) <= MAX_TAGS - len(BRAND_TAGS) else ""
    tag = r"(?<!\S)#(?=\w*[^\W\d_])\w+"  # un hashtag ha almeno una lettera: "Illusion #1" non lo è
    caption = re.sub(tag, keep, caption)
    caption = re.sub(r"[ \t]+(?=\n|$)", "", re.sub(r"(?<=\S)[ \t]{2,}", " ", caption)).rstrip()
    first = re.search(tag, caption)
    tags = " ".join(BRAND_TAGS)
    if first:
        i = first.start()
        return caption[:i] + tags + " " + caption[i:]
    return caption + "\n\n" + tags
