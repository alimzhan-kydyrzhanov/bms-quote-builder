"""Bill of materials (BOM): turn project documentation into device quantities."""
import json
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class BomResult:
    lines: pd.DataFrame                      # sku, name, category, qty, unit_price_czk, power_va
    issues: list = field(default_factory=list)  # human-readable problems for the sales engineer


def load_catalog(path):
    catalog = pd.read_csv(path)
    if catalog["sku"].duplicated().any():
        raise ValueError("Price list has duplicate SKUs")
    if (catalog["unit_price_czk"] <= 0).any():
        raise ValueError("Price list has a non-positive price")
    return catalog.set_index("sku")


def load_project(path):
    with open(path, encoding="utf-8") as f:
        project = json.load(f)
    for key in ("project", "customer", "zones"):
        if key not in project:
            raise ValueError(f"Project documentation is missing '{key}'")
    return project


def build_bom(project, catalog):
    """Multiply devices per zone by zone count; collect unknown SKUs as issues."""
    totals, per_zone, issues = {}, [], []
    for zone in project["zones"]:
        count = int(zone.get("count", 1))
        if count <= 0:
            issues.append(f"Zone '{zone['zone']}': count must be positive, skipped")
            continue
        for sku, qty in zone["devices"].items():
            if sku not in catalog.index:
                issues.append(f"Zone '{zone['zone']}': unknown SKU {sku} (x{qty * count}) - ask the designer")
                continue
            totals[sku] = totals.get(sku, 0) + qty * count
            per_zone.append({"zone": zone["zone"], "sku": sku, "qty": qty * count})

    # Every 100 VA of 24 V field devices needs one power supply (PS-24).
    load_va = sum(catalog.loc[s, "power_va"] * q for s, q in totals.items())
    if load_va and "PS-24" in catalog.index:
        totals["PS-24"] = totals.get("PS-24", 0) + -(-int(load_va) // 100)  # ceiling division

    lines = pd.DataFrame(
        [{"sku": s, "qty": q, **catalog.loc[s, ["name", "category", "unit_price_czk", "power_va", "description"]].to_dict()}
         for s, q in totals.items()]
    ).sort_values(["category", "sku"]).reset_index(drop=True)
    lines.attrs["load_va"] = load_va
    lines.attrs["per_zone"] = pd.DataFrame(per_zone)
    return BomResult(lines=lines, issues=issues)
