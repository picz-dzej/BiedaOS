import re

_AMOUNT = re.compile(r"(\d{1,3}(?:[  ]\d{3})+|\d+)(?:[.,](\d{1,2}))?")
_CURRENCY = re.compile(r"\b(zł|zl|pln)\b", re.IGNORECASE)


class ParseError(ValueError):
    pass


def parse_entry(text: str) -> tuple[str, int]:
    matches = list(_AMOUNT.finditer(text))
    if not matches:
        raise ParseError('Nie znalazłem kwoty we wpisie — dopisz ją, np. „biedronka 47,30".')
    m = matches[-1]
    whole = int(re.sub(r"[  ]", "", m.group(1)))
    frac = (m.group(2) or "0").ljust(2, "0")
    grosze = whole * 100 + int(frac)
    rest = text[: m.start()] + text[m.end():]
    rest = _CURRENCY.sub("", rest)
    desc = re.sub(r"\s+", " ", rest).strip(" ,.–-")
    return desc, grosze
