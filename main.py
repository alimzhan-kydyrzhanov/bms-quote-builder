"""CLI: project documentation + price list + CRM export -> quotation, specification, datasheets."""
import argparse
from pathlib import Path

from quote.bom import build_bom, load_catalog, load_project
from quote.documents import datasheet_md, specification_md
from quote.excel_export import write_quotation
from quote.pipeline import by_owner, kpis, load_crm
from quote.pricing import price_lines, totals


def run(project_path, catalog_path, crm_path, out_dir, discount=0.0):
    out = Path(out_dir)
    (out / "datasheets").mkdir(parents=True, exist_ok=True)
    catalog = load_catalog(catalog_path)
    project = load_project(project_path)
    bom = build_bom(project, catalog)
    priced = price_lines(bom.lines)
    crm = load_crm(crm_path) if crm_path else None
    kpi = kpis(crm) if crm is not None else None

    write_quotation(out / "quotation.xlsx", project, priced, bom.issues, kpi,
                    by_owner(crm) if crm is not None else None, discount)
    (out / "specification.md").write_text(specification_md(project, bom), encoding="utf-8")
    for sku in bom.lines["sku"]:
        (out / "datasheets" / f"{sku}.md").write_text(datasheet_md(sku, catalog.loc[sku]), encoding="utf-8")
    return {"totals": totals(priced, discount), "issues": bom.issues, "kpi": kpi}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default="data/project_hotel.json")
    ap.add_argument("--catalog", default="data/price_list.csv")
    ap.add_argument("--crm", default="data/crm_opportunities.csv")
    ap.add_argument("--out", default="output")
    ap.add_argument("--discount", type=float, default=0.03)
    a = ap.parse_args()
    res = run(a.project, a.catalog, a.crm, a.out, a.discount)
    print("Totals:", res["totals"])
    print("Open questions:", *res["issues"], sep="\n  - ")
    print("Pipeline KPIs:", res["kpi"])
