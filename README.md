# Logistics Network Solver

<img width="1873" height="502" alt="image" src="https://github.com/user-attachments/assets/a653f5d1-6376-48f7-9afa-3337cdedb52d" />

<img width="1864" height="505" alt="image" src="https://github.com/user-attachments/assets/890f6378-989a-41c0-80df-b2e2a696ef30" />

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Gurobi](https://img.shields.io/badge/Gurobi-Optimization-red.svg)](https://www.gurobi.com/)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=flat&logo=google-cloud&logoColor=white)](https://cloud.google.com/)
[![BigQuery](https://img.shields.io/badge/BigQuery-SQL-4285F4?style=flat&logo=google-cloud&logoColor=white)](https://cloud.google.com/bigquery)
[![Pandas](https://img.shields.io/badge/Pandas-Operations-150458?style=flat&logo=pandas&logoColor=white)](https://pandas.pydata.org/)

This project provides a mathematical solution to one of the most common challenges in logistics: balancing distribution center (DC) capacity with variable shipment arrival dates to eliminate detention costs.

## Key Features

 * **Dual-Engine Optimization:** Compare results between a **Greedy Heuristic** and a **Mixed-Integer Linear Programming (MILP)** model powered by **Gurobi**.
 * **ETA-Based Scheduling:** Unlike static models, this solver considers **Transit Time** (Lead Time) to ensure trucks are only dispatched when capacity is available at the destination.
 * **Soft Constraints:** Implemented slack variables to handle extreme volume surges, preventing model infeasibility while signaling the need for operational overtime.
 * **Cloud Pipeline:** Automated data flow from Python to **Google BigQuery** for real-time dashboarding.

## Impact & Results

 * **Zero Detention Costs:** The solver successfully eliminated all capacity-related fines in simulations.
 * **High Performance:** Optimized over **4.5 million decision variables** and **14,000 constraints** in under 30 seconds.
 * **Scalability:** Successfully manages nationwide logistics networks across multiple DCs (B1, B2, B3, B4, B5).

## Repository Structure

* `Base_CDs.xlsx`: Sample logistics dataset (Anonymized).
* `otm-cargas.py`: Core optimization engine using Gurobi.
* `heuristic-otm.py`: Baseline heuristic for performance comparison.
* `requirements.txt`: Project dependencies.

---
*Developed as part of the portfolio for optimization studies.*
