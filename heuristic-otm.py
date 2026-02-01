import pandas as pd
import os
from datetime import timedelta
from pandas_gbq import to_gbq

# --- CAPACITY CONFIGURATIONS ---
CAPACITY_RULES = {
    'DC B1': {'weekday': 20, 'saturday': 10, 'sunday': 0},
    'DC B2': {'weekday': 10, 'saturday': 5, 'sunday': 0},
    'DC B4': {'weekday': 16, 'saturday': 8, 'sunday': 0},
    'DC B3': {'weekday': 15, 'saturday': 8,  'sunday': 0},
    'DEFAULT': {'weekday': 10, 'saturday': 5, 'sunday': 0}
}


def get_capacity(location, date):
    """Returns max capacity based on location and day of the week."""
    weekday = date.weekday()
    rule = CAPACITY_RULES.get(location, CAPACITY_RULES['DEFAULT'])
    if weekday < 5:
        return rule['weekday']
    elif weekday == 5:
        return rule['saturday']
    else:
        return rule['sunday']


def classify_day_type(date):
    """Classifies date into weekday, sábado, or domingo for dashboard compatibility."""
    day = date.weekday()
    if day < 5:
        return 'weekday'
    elif day == 5:
        return 'saturday'
    else:
        return 'sunday'


def calculate_transit_time(km):
    """Estimates transit days based on distance (approx. 500km/day)."""
    if km == 0: return 0
    return int(km // 500) + 1


# Global Settings
CO2_FACTOR = 0.13 / 1000
DAILY_DETENTION_COST = 1000

# --- DATA LOADING AND PREPARATION ---
file_path = r'C:\Users\israb\Downloads\Base_CDs.xlsx'
df_initial = pd.read_excel(file_path, sheet_name='Planilha1')

# Ensure date format and handle missing values
df_initial['data_emissao'] = pd.to_datetime(df_initial['data_emissao'])
df_initial['peso_base'] = df_initial['peso_base'].fillna(0)
df_initial['km_rodado'] = df_initial['km_rodado'].fillna(0)

# Feature Engineering
df_initial['emissao_co2_ton'] = (df_initial['peso_base'] / 1000) * df_initial['km_rodado'] * CO2_FACTOR

# --- TRANSIT TIME CALCULATION (PRE-OPTIMIZATION) ---
df_initial['transit_time'] = df_initial['km_rodado'].apply(calculate_transit_time)
df_initial['data_chegada_prevista'] = df_initial.apply(
    lambda x: x['data_emissao'] + timedelta(days=int(x['transit_time'])), axis=1
)

# --- SCHEDULING HEURISTIC WITH TRANSIT TIME ---
schedule_registry = {}
optimized_records = []

# Sort by predicted arrival date to ensure fairness in the queue
for _, row in df_initial.sort_values('data_chegada_prevista').iterrows():
    original_arrival_date = row['data_chegada_prevista']
    destination = row['cod_destino']
    transit_days = int(row['transit_time'])

    allocated_arrival_date = None
    # Attempt to find slot within a +/- and +7 days window
    search_offsets = [0, -1, -2, 1, 2, 3, 4, 5, 6, 7]

    for offset in search_offsets:
        target_date = original_arrival_date + timedelta(days=offset)
        max_cap = get_capacity(destination, target_date)

        if max_cap > 0:
            current_occupancy = schedule_registry.get((target_date, destination), 0)
            if current_occupancy < max_cap:
                allocated_arrival_date = target_date
                break

    # Fallback: if no slot found in window, search forward until first availability
    if allocated_arrival_date is None:
        check_date = original_arrival_date + timedelta(days=1)
        while True:
            max_cap = get_capacity(destination, check_date)
            if max_cap > 0 and schedule_registry.get((check_date, destination), 0) < max_cap:
                allocated_arrival_date = check_date
                break
            check_date += timedelta(days=1)

    # Update Registry
    schedule_registry[(allocated_arrival_date, destination)] = schedule_registry.get(
        (allocated_arrival_date, destination), 0) + 1

    # Create optimized record: adjust emission date based on new arrival slot (syncing origin-destination)
    new_row = row.copy()
    new_row['data_chegada_alocada'] = allocated_arrival_date
    new_row['data_emissao'] = allocated_arrival_date - timedelta(days=transit_days)
    optimized_records.append(new_row)

df_optimized = pd.DataFrame(optimized_records)


# --- METRICS AND LOGISTICS ANALYSIS ---
def process_logistics_metrics(df, label):
    """Calculates detention costs, occupancy percentage, and formatting."""
    # Use arrival date as reference for destination occupancy
    date_ref = 'data_chegada_alocada' if 'data_chegada_alocada' in df.columns else 'data_chegada_prevista'

    # Summary for calculating daily overages
    summary = df.groupby([date_ref, 'cod_destino']).size().reset_index(name='actual_volume')
    summary['max_capacity'] = summary.apply(lambda x: get_capacity(x['cod_destino'], x[date_ref]), axis=1)
    summary['excess_volume'] = (summary['actual_volume'] - summary['max_capacity']).clip(lower=0)
    summary['daily_detention_total'] = summary['excess_volume'] * DAILY_DETENTION_COST

    # Merge back to original dataframe
    df = df.merge(summary, on=[date_ref, 'cod_destino'], how='left')
    df['custo_estadia'] = df['daily_detention_total'] / df['actual_volume']
    df['percentual_occupancy'] = (df['actual_volume'] / df['max_capacity']).replace([float('inf')], 1.0)

    # Dashboard Mapping
    df['categoria_dia'] = df[date_ref].apply(classify_day_type)
    df['tipo'] = label
    df['data_visualizacao'] = df[date_ref]

    return df.drop(columns=['actual_volume', 'max_capacity', 'excess_volume', 'daily_detention_total'])


# Process both datasets for side-by-side comparison
df_initial_processed = process_logistics_metrics(df_initial, 'heuristic_initial')
df_optimized_processed = process_logistics_metrics(df_optimized, 'heuristic_optimized')

# Final Consolidation
df_final = pd.concat([df_initial_processed, df_optimized_processed], ignore_index=True)

# --- EXPORT AND CLOUD SYNC ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r'C:\Users\israb\Downloads\otimizador-cargas-dae5eae95b7b'

to_gbq(
    df_final,
    'dataset_transportes.base_cds_consolidada',
    project_id='otimizador-cargas',
    if_exists='replace'
)

print(f"✅ Heuristic Optimization with Transit Time complete! Data pushed to BigQuery.")