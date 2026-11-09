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
- reporting the three zero-expenditure 2025 observations separately because
  they are included in descriptive statistics but omitted from the logarithmic chart

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

This program reviewed 9,112 records and detected no invalid years, invalid
spending values, or duplicate country-year entries under its validation rules.
It excluded 771 aggregate or unclassified records from country analysis. For
2025, 150 eligible country observations had average expenditure of approximately
$18.266 billion and a median of $1.285 billion; three zero-expenditure
observations are included in those statistics but omitted from the logarithmic
histogram. Worldwide expenditure increased by 57.47% between 1988 and 2025,
equivalent to compound annual growth of 1.23%. These checks assess record
consistency, not the independent accuracy of the source figures.

## Source and limitations

- Source: SIPRI Military Expenditure Database via Our World in Data.
- Limitation: Any source-specific metadata caveats (for example, carry-forward observations) should be reported with results and reviewed in the original dataset documentation.
