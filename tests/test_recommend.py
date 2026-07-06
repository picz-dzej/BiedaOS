from biedaos.recommend import recommendations, zl


def test_zl_format():
    assert zl(120000) == "1 200,00 zł"


def test_category_over_25_percent():
    recs = recommendations(1000000, {"restauracje": 300000}, {}, [])
    assert any("restauracje" in r and "30%" in r for r in recs)


def test_month_over_month_spike():
    recs = recommendations(1000000, {"rozrywka": 50000}, {"rozrywka": 20000}, [])
    assert any("rozrywka" in r and "skok" in r.lower() for r in recs)


def test_negative_balance():
    recs = recommendations(100000, {"inne": 150000}, {}, [])
    assert any("Saldo ujemne" in r for r in recs)
    assert any("Saldo ujemne (500,00 zł)" in r for r in recs)


def test_thin_buffer():
    recs = recommendations(100000, {"inne": 95000}, {}, [])
    assert any("bufor" in r.lower() for r in recs)


def test_trend_three_months():
    last3 = [(100000, 50000), (100000, 70000), (100000, 90000)]
    recs = recommendations(100000, {"inne": 20000}, {}, last3)
    assert any("trend" in r.lower() for r in recs)


def test_no_income_with_expenses():
    recs = recommendations(0, {"inne": 5000}, {}, [])
    assert any("przychodu" in r for r in recs)


def test_healthy_month():
    recs = recommendations(1000000, {"spożywcze": 200000}, {"spożywcze": 190000}, [])
    assert len(recs) == 1
    assert "80%" in recs[0]
