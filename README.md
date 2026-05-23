# BTX Process — Techno-Economic Analysis (Code Availability)

This repository contains the techno-economic analysis (TEA) modules used in the
manuscript. The modules cover the full pipeline from the hour-by-hour
product-yield evolution under catalyst deactivation, through annualization of
production and utility consumption, to a 30-year discounted cash-flow analysis
that returns the net present value (NPV) and the minimum selling price (MSP) of
benzene.

The process-simulation files (Aspen Plus) and the surrogate model used to
predict per-cycle product yields and utility duties are **not** included; the
TEA modules treat them as opaque inputs (`DATA` and `model`). This package is
intended to make the economic methodology fully transparent and reproducible
given those inputs.

---

## Modules

| File | Purpose |
|---|---|
| `catalyst_get.py` | Simulates a two-bed swing reactor hour-by-hour: linear deactivation within each cycle, regeneration at cycle boundaries, replacement when the second bed falls below `ratio * initial_yield`. Returns the per-hour yield trajectory, cycle-mean yields, the regeneration schedule, and the **annualized catalyst replacement frequency** (`replacement_per_year`). |
| `operatingcost.py` | Computes the **variable operating cost per cycle** by section (reaction, regeneration, carburization, separation), using the surrogate-predicted material and utility flows together with the unit prices in `cost_input`. Returns each section total and a detailed breakdown. |
| `operating2.py` | Computes the **fixed operating cost**: total salaries (with labor-burden), maintenance (3 % of ISBL), and property insurance (0.7 % of FCI). Labor cost is escalated by the labor-cost index. |
| `economicdata.py` | Builds the **CAPEX breakdown** from the Aspen-derived ISBL (CBM). Direct costs (warehouse, site development, additional piping) form the TDC. Indirect costs (prorateable, field, home office, contingency, others) are each 10–20 % of TDC and form the TIC. Fixed capital investment (FCI), land, working capital, and total capital investment (TCI) are then assembled. |
| `cashflow.py` | Builds the **30-year discounted cash flow** (3-year construction + 30 operating years). Includes capital disbursement (0.08/0.6/0.32), loan amortization, declining-balance depreciation (d = 0.2857, 8-year full write-off), loss carry-forward, federal tax, baghouse replacement every 5 years, catalyst replacement cost, and discounting at the project's discount rate. Returns the full year-by-year cash-flow table, NPV, and revenue breakdown. |
| `MSP.py` | Determines the **minimum selling price** of benzene as the price that makes NPV cross zero. Three-stage bracketed search: $1 → $0.01 → $0.001 step sizes. |
| `Model_GSA.py` | **Top-level orchestrator.** Calls `catalyst_get` to obtain the cycle trajectory, evaluates the surrogate model on every cycle, accumulates section costs and product flows, **annualizes** them using the cycle counts and replacement frequency, calls `operating2` for fixed OPEX, and finally invokes `MSP` and `cashflow` to obtain MSP and NPV. |

---

## Workflow

```
  catalyst_get  ────────────►  hour-by-hour yield, cycle means,
  (initial_yield, deact_r,        regeneration schedule,
   regen_r, ratio,                annual replacement count
   reaction_time)
                                       │
                                       ▼
                       per-cycle  surrogate model (user-supplied)
                                       │
                                       ▼
  operatingcost  ──────────►  variable OPEX per cycle  (reaction /
  (per-cycle predictions,                              regen / carbur /
   unit prices)                                        separation)
                                       │
                                       ▼
       Model_GSA._run_cycles  ──────►  ANNUALIZATION
                                       (Σ section cost × time × replacement
                                        frequency; regen/carbur ×2 beds)
                                       │
                                       ▼
                       annual OPEX, annual product mass
                                       │
                                       ▼
  operating2  ─────────►  fixed OPEX (labor, maintenance, insurance)
  economicdata  ──────►  FCI / TCI (direct + indirect + land + WC)
                                       │
                                       ▼
  cashflow  ──────────►  30-year CF, NPV
  MSP  ───────────────►  MSP (price at NPV = 0)
```

---

## Inputs the user must provide

`Model_GSA(model, initial_yield, deact, regen, ratio, reaction_time,
regen_time, carbur_time, COST, RESULT, DATA, catalyst_required, data_type,
rat_selling)`

* **`model`** — callable `f(x) → np.ndarray` of length 20. Input `x` is a
  length-4 vector of cycle-mean yields `[benzene, toluene, naphthalene, coke]`.
  Output indices used downstream (0-based):

  | idx | quantity |
  |---|---|
  | 0  | reaction-section CH4 material flow |
  | 1  | reaction-section fired duty |
  | 2  | regeneration fired duty |
  | 3  | regeneration cooling-water duty (cw1) |
  | 4  | regeneration cooling-water duty (cw2) |
  | 5  | regeneration electricity |
  | 6  | carburization fired duty |
  | 7  | separation HP steam |
  | 8  | separation LP steam |
  | 9  | separation cooling water |
  | 10 | separation refrigeration duty (sign determines refrigerant grade) |
  | 11 | separation electricity |
  | 12 | H2 product mass flow |
  | 13 | benzene product mass flow |
  | 14 | toluene product mass flow |
  | 15 | naphthalene product mass flow |

* **`COST`** — dictionary with keys `utility`, `chemical`, `CEPCI`,
  `IX_LABOR`, `info` containing unit prices, cost indices, and financing
  parameters (discount rate, tax rate, equity, loan term, APR, baghouse
  count/cost). Build it yourself or replicate the structure used in
  `cashflow.py`, `operatingcost.py`, and `operating2.py`.

* **`RESULT`** — dictionary that must already contain:
  * `RESULT['CAPEX']['CBM']` — ISBL CAPEX (bare-module basis) from the
    simulation. `economicdata(RESULT)` populates the rest of the CAPEX
    breakdown (`ISBL`, `FCI`, `TCI`, `TCI_land`, `TCI_working_capital`).
  * `RESULT['catalyst']` — catalyst loading (kg).

* **`DATA`** — dictionary derived from the process simulation, used only for
  two specific lookups:
  * `DATA['UNIT']['TEMP'][un.index('B11')]` — separator B11 temperature, used
    to select the refrigerant grade in `operatingcost.py`.
  * In `_calc_catalyst_cooling`: stream temperatures at the inlet/outlet of
    unit `H2`, used to estimate the catalyst cooling duty during
    regeneration. May be `None` (cooling duty is then set to 0).

* **`catalyst_required`** — catalyst mass (kg).

* **`data_type`** — kept for interface compatibility; not used in the cost
  calculations included here.

* **`rat_selling`** — multiplier on the hydrogen selling price.

---

## How `RESULT` is populated through the workflow

1. Build `RESULT['CAPEX']['CBM']` from your simulation.
2. `RESULT = economicdata(RESULT)` → adds `ISBL`, `FCI`, `TCI*`, `TCI_land`,
   `TCI_working_capital`.
3. `RESULT['catalyst'] = catalyst_required`.
4. `Model_GSA(...)` adds `yield`, `annual_operatingcost`, `annual`,
   `product_sales_summary`, and `fixed_operating_cost`, then returns the cash
   flow table, MSP, NPV, and revenue.

---

## Calling sequence

```python
from economicdata import economicdata
from Model_GSA   import Model_GSA

RESULT = {'CAPEX': {'CBM': isbl_from_simulation}, 'catalyst': catalyst_kg}
RESULT = economicdata(RESULT)

RESULT, CF, msp, npv, revenue, reaction_time = Model_GSA(
    model, initial_yield, deact_r, regen_r, ratio,
    reaction_time, regen_time, carbur_time,
    COST, RESULT, DATA, catalyst_required,
    data_type=1, rat_selling=1)
```

---

## Dependencies

```
python >= 3.9
numpy
pandas
```

`MSP.py` imports `cashflow`. `Model_GSA.py` imports `catalyst_get`,
`operatingcost`, `operating2`, `MSP`, and `cashflow`. No other inter-module
imports.

---

## What is intentionally not included

* The Aspen Plus simulation file and the COM interface that drives it.
* The neural-network surrogate model and its training data.
* Global / local sensitivity analyses and derivative-free optimization
  drivers built on top of `Model_GSA`. These can be reconstructed from the
  manuscript's methodology.

These omissions do not affect the reproducibility of the economic
calculations: any equivalent process-simulation output can be supplied
through the `model`, `DATA`, and `RESULT['CAPEX']['CBM']` interfaces.

---

## License

Released under the MIT License. See `LICENSE` for details.
