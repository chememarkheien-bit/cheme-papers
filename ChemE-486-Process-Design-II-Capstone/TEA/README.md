# Techno-Economic Analysis — Apple Pomace to Ethanol

Mark A. Heien · ChemE 486 Process Design II, University of Washington, Spring 2026 · First place, Bowen Award.

Techno-economic retrofit of Seattle's Gas Works Park into a cellulosic ethanol plant fed by Washington apple pomace.

## Start here

**[`AP_TEA_Workbook_Heien.xlsx`](AP_TEA_Workbook_Heien.xlsx)** — the working model, 22 KB, no macros. Eight sheets, 471 live formulas.

| Sheet | Contents |
|---|---|
| `AP_INPUTS` | Assumptions — CEPCI indices, discount rate, plant life, tax rate, depreciation schedule |
| `AP_CAPEX` | Equipment costing by process area; six-tenths scaling and CEPCI escalation |
| `AP_OPEX` | Annual operating cost — feedstock, transport, dilute acid, utilities, labour |
| `AP_CASHFLOW` | 20-year discounted cash flow, NPV, and minimum ethanol selling price |
| `AP_REPORT_OUTPUTS` | ISBL / FCI / TCI / MSP — the figures quoted in the written report |
| `AP_SENSITIVITY` | Tornado analysis: MSP response to capital, OPEX, yield and price |
| `AP_FORMULA_MAP` | Every costing correlation used, in plain language |
| `AP_COMPARISON` | 1900s coal-to-city-gas vs. modern pomace-to-ethanol economics |

Values-only exports of two sheets, for quick reading without opening the model:
[`AP_Inputs.xlsx`](AP_Inputs.xlsx) · [`AP_Cashflow.xlsx`](AP_Cashflow.xlsx)

Sensitivity and cash-flow figures are in [`../figures/`](../figures/).

## Provenance

The model was originally built as an added layer inside the NREL biochemical-ethanol design workbook
(`dw1910`), authored by David Humbird et al. and distributed with NREL report **NREL/TP-5100-47764**,
*Process Design and Economics for Biochemical Conversion of Lignocellulosic Biomass to Ethanol* (2011).

`AP_TEA_Workbook_Heien.xlsx` contains **only my own `AP_` sheets** — the 15 NREL worksheets and the
workbook macros are removed. My sheets reference none of the NREL sheets and no external defined names,
so the model is self-contained and computes on its own.
