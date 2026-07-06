def zl(grosze: int) -> str:
    s = f"{grosze / 100:,.2f}".replace(",", " ").replace(".", ",")
    return f"{s} zł"


def recommendations(income, by_cat, prev_by_cat, last3):
    out = []
    total = sum(by_cat.values())

    if income == 0 and total > 0:
        out.append("Nie wpisałeś przychodu w tym miesiącu — bez niego procenty i saldo nie mają sensu.")

    if income > 0:
        for cat, amount in sorted(by_cat.items(), key=lambda kv: -kv[1]):
            pct = amount / income * 100
            if pct > 25:
                out.append(f"{cat} zjada {pct:.0f}% przychodu ({zl(amount)}).")

    for cat, amount in by_cat.items():
        prev = prev_by_cat.get(cat, 0)
        if prev > 0 and amount - prev > 10000 and (amount - prev) / prev > 0.30:
            out.append(
                f"{cat}: skok o {(amount - prev) / prev * 100:.0f}% względem "
                f"poprzedniego miesiąca ({zl(prev)} → {zl(amount)})."
            )

    if income > 0 and total > income:
        out.append(
            f"Saldo ujemne ({zl(income - total)}). To problem poziomu przychodu albo "
            "stałej struktury wydatków — nie pojedynczych zakupów."
        )
    elif income > 0 and total > income * 0.9:
        out.append("Zostaje mniej niż 10% bufora. Jeden nieprzewidziany wydatek zjada cały zapas.")

    if len(last3) == 3 and all(i > 0 for i, _ in last3):
        inc_growth = last3[-1][0] - last3[0][0]
        exp_growth = last3[-1][1] - last3[0][1]
        if exp_growth > 0 and exp_growth > inc_growth:
            out.append("Od trzech miesięcy wydatki rosną szybciej niż przychody — to trend, nie przypadek.")

    if not out and income > 0:
        rate = (income - total) / income * 100
        out.append(f"Wygląda zdrowo. Stopa oszczędności: {rate:.0f}%.")
    return out
