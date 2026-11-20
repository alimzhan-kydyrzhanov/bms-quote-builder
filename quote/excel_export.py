"""Excel quotation workbook with live formulas (the customer/sales team can edit qty or price)."""
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from quote.pricing import VAT_RATE

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF")
THIN = Side(style="thin", color="BFBFBF")
CZK = '#,##0.00 "CZK"'


def _header(ws, row, titles, widths):
    for col, (title, width) in enumerate(zip(titles, widths), start=1):
        c = ws.cell(row=row, column=col, value=title)
        c.fill, c.font, c.alignment = HEADER_FILL, HEADER_FONT, Alignment(horizontal="center")
        ws.column_dimensions[get_column_letter(col)].width = width


def write_quotation(path, project, priced, issues, kpi=None, owners=None, project_discount=0.0):
    wb = Workbook()
    ws = wb.active
    ws.title = "Quotation"
    ws["A1"] = f"Quotation - {project['project']}"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Customer: {project['customer']}"

    _header(ws, 4, ["SKU", "Device", "Qty", "Unit price", "Discount", "Line total"], [10, 34, 8, 16, 10, 18])
    first = 5
    for i, r in enumerate(priced.itertuples(), start=first):
        ws.append([r.sku, r.name, r.qty, r.unit_price_czk, r.discount])
        ws.cell(row=i, column=6, value=f"=C{i}*D{i}*(1-E{i})")  # formula, not a hard-coded number
        ws.cell(row=i, column=4).number_format = CZK
        ws.cell(row=i, column=5).number_format = "0%"
        ws.cell(row=i, column=6).number_format = CZK
        for col in range(1, 7):
            ws.cell(row=i, column=col).border = Border(bottom=THIN)
    last = first + len(priced) - 1

    t = last + 2
    rows = [
        ("Subtotal", f"=SUM(F{first}:F{last})"),
        ("Project discount", project_discount),
        ("Net total", f"=F{t}*(1-F{t + 1})"),
        (f"VAT {VAT_RATE:.0%}", f"=F{t + 2}*{VAT_RATE}"),
        ("Total incl. VAT", f"=F{t + 2}+F{t + 3}"),
    ]
    for k, (label, value) in enumerate(rows):
        ws.cell(row=t + k, column=5, value=label).font = Font(bold=True)
        c = ws.cell(row=t + k, column=6, value=value)
        c.number_format = "0%" if label == "Project discount" else CZK
    ws.cell(row=t + 4, column=6).font = Font(bold=True)
    ws.freeze_panes = "A5"

    wi = wb.create_sheet("Open questions")
    _header(wi, 1, ["#", "Issue for designer / sales engineer"], [5, 90])
    for n, text in enumerate(issues or ["No open questions"], start=1):
        wi.append([n, text])

    if kpi is not None:
        wk = wb.create_sheet("Pipeline KPIs")
        _header(wk, 1, ["KPI", "Value"], [28, 18])
        for k, v in kpi.items():
            wk.append([k.replace("_", " "), v])
        if owners is not None:
            start = len(kpi) + 3
            _header(wk, start, ["Owner", "Deals", "Won", "Weighted pipeline CZK"], [28, 18, 10, 24])
            for r in owners.itertuples(index=False):
                wk.append(list(r))
    wb.save(path)
    return path
