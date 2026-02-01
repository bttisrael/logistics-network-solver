# Logistics Network Solver

<img width="1873" height="502" alt="image" src="https://github.com/user-attachments/assets/a653f5d1-6376-48f7-9afa-3337cdedb52d" />

<img width="1864" height="505" alt="image" src="https://github.com/user-attachments/assets/890f6378-989a-41c0-80df-b2e2a696ef30" />



This project provides a mathematical solution to one of the most common challenges in logistics: balancing distribution center (DC) capacity with variable shipment arrival dates to eliminate detention costs.

## Key Features

 * **Dual-Engine Optimization:** Compare results between a **Greedy Heuristic** and a **Mixed-Integer Linear Programming (MILP)** model powered by **Gurobi**.
 * **ETA-Based Scheduling:** Unlike static models, this solver considers **Transit Time** (Lead Time) to ensure trucks are only dispatched when capacity is available at the destination.
 * **Soft Constraints:** Implemented slack variables to handle extreme volume surges, preventing model infeasibility while signaling the need for operational overtime.
 * **Cloud Pipeline:** Automated data flow from Python to **Google BigQuery** for real-time dashboarding.

## Stack

 * **Optimization:** Gurobi (State-of-the-art MILP solver)
 * **Language:** Python (Pandas, Numpy)
 * **Cloud/BI:** BigQuery (GCP), Looker Studio
 * **Mathematical Modeling:** Constraint Satisfaction and Linear Programming

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
