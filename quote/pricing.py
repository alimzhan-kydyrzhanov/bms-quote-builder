"""Pricing rules: volume discount per line, project discount, VAT."""
VAT_RATE = 0.21  # Czech standard VAT
VOLUME_TIERS = [(50, 0.10), (20, 0.05)]  # qty >= 50 -> 10 %, qty >= 20 -> 5 %


def line_discount(qty):
    for min_qty, rate in VOLUME_TIERS:
        if qty >= min_qty:
            return rate
    return 0.0


def price_lines(lines):
    """Add discount and line totals (the same maths the Excel formulas do)."""
    df = lines.copy()
    df["discount"] = df["qty"].apply(line_discount)
    df["line_total_czk"] = (df["qty"] * df["unit_price_czk"] * (1 - df["discount"])).round(2)
    return df


def totals(priced, project_discount=0.0):
    if not 0 <= project_discount < 0.5:
        raise ValueError("Project discount must be between 0 and 50 %")
    net = round(float(priced["line_total_czk"].sum() * (1 - project_discount)), 2)
    vat = round(net * VAT_RATE, 2)
    return {"net_czk": net, "vat_czk": vat, "gross_czk": round(net + vat, 2)}
