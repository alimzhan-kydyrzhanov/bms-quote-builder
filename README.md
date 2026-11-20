# Building Automation Quotation Builder

A small sales-operations tool: it reads **project documentation** for a building automation
project (a hotel retrofit), builds the **bill of materials**, prices it, and produces:

- `output/quotation.xlsx` - Excel quotation with live formulas (line totals, discount, VAT 21 %),
  an "Open questions" sheet and a "Pipeline KPIs" sheet;
- `output/specification.md` - technical specification for the designer: device list, devices per zone,
  24 V AC power calculation (how many power supplies are needed);
- `output/datasheets/*.md` - one product datasheet per device for sales / marketing.

It also analyses a **CRM opportunity export** (win rate, open and weighted pipeline, sales cycle, per owner).

All data is synthetic.

## Run

```bash
pip install -r requirements.txt
python -m pytest -q
python main.py                 # default: 3 % project discount
python main.py --discount 0.05
```

Docker:

```bash
docker build -t quote-builder .
docker run --rm -v "$PWD/output:/app/output" quote-builder
```

## Structure

| File | What it does |
|---|---|
| `data/project_hotel.json` | Project documentation: zones, how many of each, devices per zone |
| `data/price_list.csv` | Product catalog: price, power draw, description |
| `data/crm_opportunities.csv` | CRM export of sales opportunities |
| `quote/bom.py` | Project documentation -> quantities; unknown SKUs become open questions; power supply sizing |
| `quote/pricing.py` | Volume discounts, project discount, VAT |
| `quote/excel_export.py` | Excel workbook with formulas and formatting (openpyxl) |
| `quote/documents.py` | Technical specification and product datasheets (Markdown) |
| `quote/pipeline.py` | Sales pipeline KPIs from the CRM export |
| `main.py` | Command-line entry point |
| `tests/test_quote.py` | pytest unit + end-to-end tests |
