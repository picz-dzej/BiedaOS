import pytest
from biedaos.parsing import ParseError, parse_entry


@pytest.mark.parametrize("text,desc,grosze", [
    ("biedronka 47,30", "biedronka", 4730),
    ("paliwo 250", "paliwo", 25000),
    ("czynsz 1 200 zł", "czynsz", 120000),
    ("czynsz 1 200 zł", "czynsz", 120000),
    ("2 piwa 15.5", "2 piwa", 1550),
    ("wypłata 5000,00", "wypłata", 500000),
    ("40 kebab", "kebab", 4000),
])
def test_parse_entry(text, desc, grosze):
    assert parse_entry(text) == (desc, grosze)


def test_no_amount_raises():
    with pytest.raises(ParseError):
        parse_entry("zakupy w biedronce")


def test_empty_description_allowed():
    assert parse_entry("50") == ("", 5000)
