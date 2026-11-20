"""Documents for designers and marketing: technical specification + product datasheets."""
from datetime import date


def specification_md(project, bom):
    lines = bom.lines
    per_zone = lines.attrs["per_zone"]
    out = [
        f"# Technical Specification - {project['project']}",
        f"Customer: {project['customer']}  |  Designer: {project.get('designer', '-')}  |  Date: {date.today()}",
        "",
        "## 1. Device list",
        "| SKU | Device | Qty | Description |",
        "|---|---|---:|---|",
    ]
    for r in lines.itertuples():
        out.append(f"| {r.sku} | {r.name} | {r.qty} | {r.description} |")

    out += ["", "## 2. Devices per zone", "| Zone | SKU | Qty |", "|---|---|---:|"]
    for r in per_zone.itertuples():
        out.append(f"| {r.zone} | {r.sku} | {r.qty} |")

    load = lines.attrs["load_va"]
    ps = int(lines.loc[lines["sku"] == "PS-24", "qty"].sum())
    out += [
        "",
        "## 3. 24 V AC power calculation",
        f"Total field-device load: **{load} VA**. Power supplies PS-24 (100 VA each): **{ps}**, "
        f"loading {load / (ps * 100):.0%} of capacity." if ps else "No 24 V devices.",
    ]
    if bom.issues:
        out += ["", "## 4. Open questions for the designer"] + [f"- {i}" for i in bom.issues]
    return "\n".join(out) + "\n"


def datasheet_md(sku, row):
    """One-page product datasheet used by sales and marketing (MarCom)."""
    return (
        f"# {row['name']}\n\n"
        f"**SKU:** {sku}  |  **Category:** {row['category']}\n\n"
        f"{row['description']}.\n\n"
        f"- Power consumption: {row['power_va']} VA\n"
        f"- List price: {row['unit_price_czk']:,.0f} CZK (excl. VAT)\n"
    )
