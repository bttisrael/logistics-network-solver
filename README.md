
# Logistics Network Solver: Multi-DC Capacity & Freight Optimization

<img width="100%" alt="Logistics Dashboard Preview" src="https://github.com/user-attachments/assets/a653f5d1-6376-48f7-9afa-3337cdedb52d" />

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Gurobi](https://img.shields.io/badge/Gurobi-Optimization-red.svg)](https://www.gurobi.com/)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=flat&logo=google-cloud&logoColor=white)](https://cloud.google.com/)
[![BigQuery](https://img.shields.io/badge/BigQuery-SQL-4285F4?style=flat&logo=google-cloud&logoColor=white)](https://cloud.google.com/bigquery)
[![Looker Studio](https://img.shields.io/badge/Looker_Studio-BI-4285F4?style=flat&logo=looker&logoColor=white)](https://lookerstudio.google.com/)

## Introduction

The **Logistics-Network-Solver** provides a robust mathematical solution to one of the most complex challenges in modern supply chain: balancing Distribution Center (DC) receiving capacity with variable shipment arrival dates to eliminate detention costs.

This project implements an optimization pipeline that accounts for **Transit Time** (Lead Time) between origin and destination, ensuring that freight flow is dictated by the actual absorption capacity of the network. The solution allows for a performance comparison between simple heuristics and high-complexity mathematical modeling via Mixed-Integer Linear Programming (MILP).

## Features

* **Dual-Engine Optimization:** Direct comparison between a **Greedy Heuristic** and a **MILP** mathematical model using the Gurobi solver.
* **ETA-Based Scheduling:** The model projects arrival dates at the destination to ensure that the DC's daily capacity is never breached.
* **Soft Constraints:** Implementation of slack variables to handle extreme volume surges, signaling the need for operational overtime instead of causing model infeasibility.
* **Cloud Native Pipeline:** Automated data flow from Python to **Google BigQuery** for executive consumption via Looker Studio dashboards.

## Installation

Clone and install the dependencies. Ensure you have Gurobi installed for the exact optimization engine.

```bash
git clone [https://github.com/bttisrael/logistics-network-solver.git](https://github.com/bttisrael/logistics-network-solver.git)
cd logistics-network-solver
pip install -r requirements.txt
```

## Usage & Sample Code
The core optimization engine formulates the problem as a minimization of delay and capacity costs. Below is an example of the DC capacity constraint implementation found in the otm-cargas.py engine:

```Python
import gurobipy as gp
from gurobipy import GRB

# Dynamic capacity definition by unit and day type
CAPACITY_RULES = {
    'DC B1': {'weekday': 20, 'saturday': 10, 'sunday': 0},
    'DC B4': {'weekday': 16, 'saturday': 8, 'sunday': 0},
    'DEFAULT': {'weekday': 10, 'saturday': 5, 'sunday': 0}
}

# Gurobi Model Initialization
model = gp.Model("Logistics_Optimization")

# Constraint: Total load destined for DC 'j' on day 't' must not exceed capacity
for j in destinations:
    for t in dates:
        model.addConstr(gp.quicksum(x[i, t] for i in loads_to_j) <= max_cap[j, t], name=f"Capacity_{j}_{t}")

model.optimize()
```
## Experiments and Diagnostics
Stress tests and business diagnostics performed on the pipeline yielded the following performance indicators:

* **Scalability**: The solver optimized over 4.5 million decision variables and 14,000 constraints in under 30 seconds.

* **Cost Reduction**: Successfully eliminated 100% of detention fines in simulations with the MILP engine compared to the historical baseline.

* **Exception Management**: Clear identification of critical bottlenecks in DCs B1 and B4 during promotional periods, allowing for proactive extra slot planning.

## Reference
[1] Gurobi Optimization, LLC. (2023). Gurobi Optimizer Reference Manual.

[2] Chopra, S., & Meindl, P. (2016). Supply Chain Management: Strategy, Planning, and Operation.

[2] Gurobi Optimization, LLC. (2023). Gurobi Optimizer Reference Manual.

[3] Chopra, S., & Meindl, P. (2016). Supply Chain Management: Strategy, Planning, and Operation.
