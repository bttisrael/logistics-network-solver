import gurobipy as gp
from gurobipy import GRB
from datetime import timedelta
import pandas as pd
import os
from pandas_gbq import to_gbq

# --- ENVIRONMENT CONFIGURATION ---
try:
    # Initialize Gurobi environment (automatically detects local .lic file)
    env = gp.Env()
    print("✅ Gurobi environment started.")
except gp.GurobiError:
    # Fallback initialization
    env = gp.Env()

# --- CAPACITY RULES & HELPER FUNCTIONS ---
CAPACITY_RULES = {
    'DC B1': {'weekday': 20, 'saturday': 10, 'sunday': 0},
    'DC B2': {'weekday': 10, 'saturday': 5, 'sunday': 0},
    'DC B4': {'weekday': 16, 'saturday': 8, 'sunday': 0},
    'DC B3': {'weekday': 15, 'saturday': 8,  'sunday': 0},
    'DEFAULT': {'weekday': 10, 'saturday': 5, 'sunday': 0}
}

def get_capacity(location, date):
    """Retrieves the maximum shipment capacity for a specific DC and date."""
    weekday = date.weekday()
    rule = CAPACITY_RULES.get(location, CAPACITY_RULES['DEFAULT'])
    if weekday < 5:
        return rule['weekday']
    elif weekday == 5:
        return rule['saturday']
    else:
        return rule['sunday']

def classify_day_type(date):
    """Classifies the date for dashboard filtering (sábado/domingo/weekday)."""
    day = date.weekday()
    if day < 5:
        return 'weekday'
    elif day == 5:
        return 'saturday'
    else:
        return 'sunday'

def calculate_transit_time(km):
    """Estimates transit time: 500km per day + 1 day for loading/unloading."""
    if km == 0: return 0
    return int(km // 500) + 1

# --- DATA LOADING & PREPARATION ---
file_path = r'C:\Users\israb\Downloads\Base_CDs.xlsx'
df_raw = pd.read_excel(file_path, sheet_name='Planilha1')

# Global Logistics Constants
CO2_FACTOR = 0.13 / 1000
DAILY_DETENTION_COST = 1000

# Initial Data Cleaning & Feature Engineering
df_raw['data_emissao'] = pd.to_datetime(df_raw['data_emissao'])
df_raw['peso_base'] = df_raw['peso_base'].fillna(0)
df_raw['km_rodado'] = df_raw['km_rodado'].fillna(0)
df_raw['emissao_co2_ton'] = (df_raw['peso_base'] / 1000) * df_raw['km_rodado'] * CO2_FACTOR

# --- TRANSIT TIME & ETA CALCULATION ---
# We calculate 'data_chegada_prevista' (ETA) as the target for DC occupancy
df_raw['transit_time'] = df_raw['km_rodado'].apply(calculate_transit_time)
df_raw['data_chegada_prevista'] = df_raw.apply(
    lambda x: x['data_emissao'] + timedelta(days=int(x['transit_time'])), axis=1
)

# --- MATHEMATICAL OPTIMIZATION (GUROBI) ---
model = gp.Model("DC_Scheduling_Optimization_with_Transit", env=env)

shipments = df_raw.index.tolist()

# Define planning horizon based on arrival dates
min_date = df_raw['data_chegada_prevista'].min() - timedelta(days=2)
max_date = df_raw['data_chegada_prevista'].max() + timedelta(days=10)
available_dates = pd.date_range(min_date, max_date)

# Decision Variable: x[s, d] is 1 if shipment 's' is assigned to arrive on date 'd'
x = model.addVars(shipments, available_dates, vtype=GRB.BINARY, name="x")

# Constraint 1: Every shipment must be allocated to exactly one arrival date
model.addConstrs((x.sum(s, '*') == 1 for s in shipments), name="unique_allocation")

# Constraint 2: DC Capacity Limits per Day (based on arrival date)
for d in available_dates:
    for location in df_raw['cod_destino'].unique():
        ship_per_location = df_raw[df_raw['cod_destino'] == location].index.tolist()
        max_cap = get_capacity(location, d)
        model.addConstr(
            gp.quicksum(x[s, d] for s in ship_per_location) <= max_cap,
            name=f"cap_{location}_{d.strftime('%Y%m%d')}"
        )

# Objective Function: Minimize absolute deviation between Actual Arrival and Predicted ETA
obj = gp.quicksum(
    x[s, d] * abs((d - df_raw.loc[s, 'data_chegada_prevista']).days)
    for s in shipments for d in available_dates
)
model.setObjective(obj, GRB.MINIMIZE)

# Solve Model
model.optimize()

# --- RESULTS EXTRACTION ---
optimized_records = []
if model.status == GRB.OPTIMAL:
    for s in shipments:
        for d in available_dates:
            if x[s, d].X > 0.5:
                row = df_raw.loc[s].copy()
                transit_days = int(row['transit_time'])

                # Update output columns
                row['data_chegada_alocada'] = d
                # Sync Origin: Adjust emission date based on new arrival slot
                row['data_emissao'] = d - timedelta(days=transit_days)
                optimized_records.append(row)

df_optimized = pd.DataFrame(optimized_records)

# --- METRICS CALCULATION ---
def process_logistics_metrics(df, label):
    """Calculates final logistics KPIs for Dashboard visualization."""
    # reference arrival date for occupancy metrics
    date_ref = 'data_chegada_alocada' if 'data_chegada_alocada' in df.columns else 'data_chegada_prevista'

    # Daily aggregation for capacity analysis
    summary = df.groupby([date_ref, 'cod_destino']).size().reset_index(name='actual_volume')
    summary['cap_maxima'] = summary.apply(lambda x: get_capacity(x['cod_destino'], x[date_ref]), axis=1)
    summary['excess_volume'] = (summary['actual_volume'] - summary['cap_maxima']).clip(lower=0)
    summary['total_daily_cost'] = summary['excess_volume'] * DAILY_DETENTION_COST

    # Merge results back to main dataframe
    df = df.merge(summary, on=[date_ref, 'cod_destino'], how='left')
    df['custo_estadia'] = df['total_daily_cost'] / df['actual_volume']
    df['percentual_ocupacao'] = (df['actual_volume'] / df['cap_maxima']).replace([float('inf')], 1.0)
    df['categoria_dia'] = df[date_ref].apply(classify_day_type)
    df['tipo'] = label

    # Standardize Date column for BigQuery/Looker Studio
    df['data_visualizacao'] = df[date_ref]
    return df

# Process both datasets
df_initial_proc = process_logistics_metrics(df_raw, 'base_inicial')
df_optimized_proc = process_logistics_metrics(df_optimized, 'base_otimizada')

# Combine and Export
df_final = pd.concat([df_initial_proc, df_optimized_proc], ignore_index=True)

# --- CLOUD EXPORT ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r'C:\Users\israb\Downloads\otimizador-cargas-dae5eae95b7b'
to_gbq(
    df_final,
    'dataset_transportes.base_cds_consolidada',
    project_id='otimizador-cargas',
    if_exists='replace'
)

print("✅ Gurobi Transit Time Optimization finished and data synced to BigQuery!")