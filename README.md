# Validating International Military Expenditure Data with Python

This project turns military-spending analysis into a reproducible **data-quality and validation** workflow.

## What the program does

`validate_military_expenditure.py` checks and analyzes SIPRI/OWID military expenditure data by:

- validating required fields (`Entity`, `Year`, `Military expenditure`)
- flagging invalid years, missing/non-finite/negative spending values, and duplicate country-year records
- separating country observations from regional/world aggregates so totals are not double-counted as countries
- reproducing 2025 country-level summary statistics (count, mean, median, standard deviation)
- computing world-level growth metrics from observed values:
  - percentage growth from first to last observed year
  - compound annual growth rate (CAGR)
- generating a 2025 country expenditure distribution chart

## Run

```bash
python validate_military_expenditure.py \
  --input /absolute/path/to/military-spending-sipri.zip
```

You can also pass a CSV directly:

```bash
python validate_military_expenditure.py \
  --input /absolute/path/to/military-spending-sipri.csv
```

Optional arguments:

- `--output-chart /absolute/path/to/chart.png`
- `--population-std` (uses population standard deviation; default is sample standard deviation)

## Plain-language interpretation

This program checks a military-spending dataset for missing, duplicate, and invalid records before calculating summary results. It separates country records from aggregate totals and then shows how spending is distributed across countries in 2025. It also calculates long-term growth using the first and last observed world values so trend results are based on actual data, not hard-coded figures.

## Source and limitations

- Source: SIPRI Military Expenditure Database via Our World in Data.
- Limitation: Any source-specific metadata caveats (for example, carry-forward observations) should be reported with results and reviewed in the original dataset documentation.
