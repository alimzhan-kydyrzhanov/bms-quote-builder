import json

import pandas as pd
import pytest
from openpyxl import load_workbook

from main import run
from quote.bom import build_bom, load_catalog, load_project
from quote.pipeline import kpis, load_crm
from quote.pricing import line_discount, price_lines, totals

CATALOG, PROJECT, CRM = "data/price_list.csv", "data/project_hotel.json", "data/crm_opportunities.csv"


@pytest.fixture
def bom():
    return build_bom(load_project(PROJECT), load_catalog(CATALOG))


def test_quantities_multiply_by_zone_count(bom):
    qty = dict(zip(bom.lines["sku"], bom.lines["qty"]))
    assert qty["RC-100"] == 12 + 12 + 2 + 2
    assert qty["VA-24"] == 24 * 2 + 2 * 2 + 4


def test_unknown_sku_becomes_issue_not_crash(bom):
    assert any("LX-99" in i for i in bom.issues)
    assert "LX-99" not in set(bom.lines["sku"])


def test_power_supplies_cover_load(bom):
    ps = int(bom.lines.loc[bom.lines["sku"] == "PS-24", "qty"].iloc[0])
    assert ps * 100 >= bom.lines.attrs["load_va"] > (ps - 1) * 100


@pytest.mark.parametrize("qty,rate", [(1, 0), (19, 0), (20, 0.05), (50, 0.10)])
def test_volume_discount_tiers(qty, rate):
    assert line_discount(qty) == rate


def test_totals_include_vat():
    lines = pd.DataFrame({"sku": ["A"], "qty": [2], "unit_price_czk": [100.0]})
    t = totals(price_lines(lines))
    assert t == {"net_czk": 200.0, "vat_czk": 42.0, "gross_czk": 242.0}


def test_invalid_discount_rejected():
    with pytest.raises(ValueError):
        totals(price_lines(pd.DataFrame({"qty": [1], "unit_price_czk": [1.0]})), 0.9)


def test_missing_project_key(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"project": "x"}))
    with pytest.raises(ValueError):
        load_project(p)


def test_crm_kpis():
    k = kpis(load_crm(CRM))
    assert k["win_rate"] == 0.6                       # 3 won of 5 closed
    assert k["open_pipeline_czk"] == 2100000 + 830000 + 3400000 + 1180000 + 720000


def test_end_to_end_excel_has_formulas(tmp_path):
    res = run(PROJECT, CATALOG, CRM, tmp_path, 0.03)
    ws = load_workbook(tmp_path / "quotation.xlsx")["Quotation"]
    assert str(ws["F5"].value).startswith("=C5*D5")
    assert (tmp_path / "specification.md").read_text().count("PS-24") >= 1
    assert res["totals"]["gross_czk"] > res["totals"]["net_czk"]
