# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "d09128bc-ca6e-4969-8471-d8f6d7a505ea",
# META       "default_lakehouse_name": "paydataplat_lakehouse",
# META       "default_lakehouse_workspace_id": "0c0f787a-053e-4b50-93e2-ba2559787ca1",
# META       "known_lakehouses": [
# META         {
# META           "id": "d09128bc-ca6e-4969-8471-d8f6d7a505ea"
# META         }
# META       ]
# META     },
# META     "environment": {
# META       "environmentId": "7b1fadb5-76da-4419-8ea3-1c38a963625c",
# META       "workspaceId": "cc7a6b09-02aa-4f0d-9ba0-55373bffcab1"
# META     }
# META   }
# META }

# MARKDOWN ********************

# # RunLoadTest - Parameterized Sessions
# 
# Load test with date parameterization for cache bypass.
# Each session uses unique date parameters to avoid query cache hits.

# CELL ********************

# Imports
import uuid
import copy
import glob
import json
import os
import re
import time
import sys

import numpy as np
import pandas as pd
import polars as pl
import sempy.fabric as fabric
import notebookutils
import ipywidgets as widgets
from IPython.display import display
from datetime import datetime, date, timezone, timedelta as td
from datetime import datetime as dt
from deltalake import DeltaTable
from deltalake.writer import write_deltalake

# Load Test Telemetry
sys.path.insert(0, '/lakehouse/default/Files/test/PerfScenarios/lib')
from applicationinsights import TelemetryClient
from FabricLoadTestTelemetry import send_loadtest_telemetry

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Configuration Widgets
# Session configuration

pst_tz = timezone(td(hours=-8))
today_pst = datetime.now(pst_tz).date()

# Test label is required for telemetry logging
test_label_input = widgets.Text(
    value='',
    description='Test Label:',
    placeholder='e.g., Baseline, Enhancement',
    style={'description_width': 'initial'}
)

# Environment selection
environment_dropdown = widgets.Dropdown(
    options=[('Test', 'Payments @ Microsoft [Test]'),
             ('Prod', 'Payments @ Microsoft [Prod]')],
    value='Payments @ Microsoft [Test]',
    description='Environment:',
    style={'description_width': 'initial'}
)

concurrent_users_dropdown = widgets.Dropdown(
    options=[1, 2, 3, 5, 10],
    value=1,
    description='Sessions:',
    style={'description_width': 'initial'}
)

execution_mode_dropdown = widgets.Dropdown(
    options=[('Parallel (queries run simultaneously)', False),
             ('Sequential (queries run one-by-one)', True)],
    value=True,
    description='Query Mode:',
    style={'description_width': 'initial'}
)

max_parallel_dropdown = widgets.Dropdown(
    options=[5, 10, 15, 20, 25],
    value=10,
    description='Max Parallel:',
    style={'description_width': 'initial'}
)

# Query date configuration - Start and End dates
query_start_date = widgets.DatePicker(
    description='Start Date:',
    value=date(2023, 10, 1),
    style={'description_width': 'initial'}
)

query_end_date = widgets.DatePicker(
    description='End Date:',
    value=today_pst,
    style={'description_width': 'initial'}
)

# Period Type dropdown - affects data aggregation granularity
period_type_dropdown = widgets.Dropdown(
    options=['Daily', 'Weekly', 'Monthly', 'Quarterly'],
    value='Weekly',
    description='Period Type:',
    style={'description_width': 'initial'}
)

# Iterations - how many sequential DAG executions per session
iterations_dropdown = widgets.Dropdown(
    options=[1, 2, 3, 5, 10, 15, 20, 25],
    value=3,
    description='Iterations:',
    style={'description_width': 'initial'}
)
# Cache clearing options
clear_aas_cache_checkbox = widgets.Checkbox(
    value=True,
    description='Clear AAS Cache per iteration',
    style={'description_width': 'initial'}
)

refresh_fabric_checkbox = widgets.Checkbox(
    value=True,
    description='Trigger Fabric Refresh (async - reloads from Kusto/Synapse)',
    style={'description_width': 'initial'}
)

print("⚠️  Test Label (REQUIRED)")
print("-" * 40)
display(test_label_input)

# Display widgets in logical order
print("Load Test Configuration")
print("-" * 40)
display(test_label_input)
display(environment_dropdown)
display(concurrent_users_dropdown)
display(execution_mode_dropdown)
display(max_parallel_dropdown)

print("\nIteration Settings")
print("-" * 40)
display(iterations_dropdown)
print("Note: Stats (avg, p50, p90, p95, p99) computed at SESSION level after all iterations")

print("\nQuery Date Range Settings")
print("-" * 40)
display(query_start_date)
display(query_end_date)
display(period_type_dropdown)

print("\nCache Settings")
print("-" * 40)
display(clear_aas_cache_checkbox)
display(refresh_fabric_checkbox)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Build Load Test Configuration

num_sessions = concurrent_users_dropdown.value
num_iterations = iterations_dropdown.value
parallel_queries = execution_mode_dropdown.value
max_parallel = max_parallel_dropdown.value
start_date = query_start_date.value
end_date = query_end_date.value
period_type = period_type_dropdown.value
workspace = environment_dropdown.value
test_label = test_label_input.value.strip()
# VALIDATION
if not test_label:
    raise ValueError("Test Label is required")
if end_date <= start_date:
    raise ValueError("End date must be after start date")

load_test_name = "Payments Performance Test"
dataset = "Payment Analytics Dataset"
# workspace = "Payments @ Microsoft [Test]"
query_folder = "/lakehouse/default/Files/test/PerfScenarios/Queries"
source_file = f"{query_folder}/PowerBIPerformanceData_Parameterized_New.json"
query_file = f"{query_folder}/PowerBIPerformanceData_Runtime.json"
iterations = 1

# Regex patterns for date parameterization
START_DATE_PATTERN = r">=\s*DATE\s*\(\s*\d{4}\s*,\s*\d{1,2}\s*,\s*\d{1,2}\s*\)"
END_DATE_PATTERN = r"<\s*DATE\s*\(\s*\d{4}\s*,\s*\d{1,2}\s*,\s*\d{1,2}\s*\)"
PERIOD_TYPE_PATTERN = r'TREATAS\s*\(\s*\{"(?:Daily|Weekly|Monthly|Yearly)"\}\s*,\s*\'DimRelativeDate\'\[Type\]\)'

# Build replacement strings
new_start_date_str = f">= DATE({start_date.year}, {start_date.month}, {start_date.day})"
end_date_exclusive = end_date + td(days=1)
new_end_date_str = f"< DATE({end_date_exclusive.year}, {end_date_exclusive.month}, {end_date_exclusive.day})"
new_period_type_str = f'TREATAS({{"{period_type}"}}, \'DimRelativeDate\'[Type])'

# Read and parameterize the source file
with open(source_file, 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

total_queries, start_modified, end_modified, period_modified = 0, 0, 0, 0
for event in data.get('events', []):
    if event.get('name') == 'Execute DAX Query':
        total_queries += 1
        query_text = event.get('metrics', {}).get('QueryText', '')
        if query_text:
            if re.search(START_DATE_PATTERN, query_text):
                query_text = re.sub(START_DATE_PATTERN, new_start_date_str, query_text)
                start_modified += 1
            if re.search(END_DATE_PATTERN, query_text):
                query_text = re.sub(END_DATE_PATTERN, new_end_date_str, query_text)
                end_modified += 1
            if re.search(PERIOD_TYPE_PATTERN, query_text):
                query_text = re.sub(PERIOD_TYPE_PATTERN, new_period_type_str, query_text)
                period_modified += 1
            event['metrics']['QueryText'] = query_text

# Write parameterized runtime file
with open(query_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

# Create load test ID and folder
ts = time.strftime("%Y%m%d-%H%M%S")
loadtestId = f"{load_test_name}-{ts}"
folder_path = f"/lakehouse/default/Files/test/PerfScenarios/logs/{loadtestId}"
notebookutils.fs.mkdirs(f"Files/test/PerfScenarios/logs/{loadtestId}")

# Base args for DAG
base_args = {
    "xmla_endpoint": f"powerbi://api.powerbi.com/v1.0/myorg/{workspace}",
    "model": dataset,
    "roles": None,
    "customdata": None,
    "effective_username": None,
    "iterations": iterations,
    "delay_sec": 1,
    "loadtestId": loadtestId,
    "concurrent_threads": num_sessions,
    "useRootDefaultLakehouse": True,
    "parallel_queries": parallel_queries,
    "max_parallel_queries": max_parallel,
    "perf_analyzer_filename": query_file
}

# Print summary
print(f"Load Test: {loadtestId}")
print(f"  Test Label: {test_label}")
print(f"  Workspace: {workspace}")
print(f"  Sessions: {num_sessions} | Iterations: {num_iterations} | Queries: {total_queries}")
print(f"  Dates: {start_date} to {end_date} | Period: {period_type}")
print(f"  Cache Clear: {clear_aas_cache_checkbox.value} | Fabric Refresh: {refresh_fabric_checkbox.value}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Execute Load Test Session

clear_cache_per_iter = clear_aas_cache_checkbox.value
refresh_fabric_per_iter = refresh_fabric_checkbox.value
num_concurrent_users = num_sessions

def shift_dates_in_runtime_json(runtime_json: dict, day_offset: int) -> dict:
    shifted = copy.deepcopy(runtime_json)
    START_PATTERN = r">=\s*DATE\s*\(\s*(\d{4})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})\s*\)"
    END_PATTERN = r"<\s*DATE\s*\(\s*(\d{4})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})\s*\)"
    
    def shift_start(match):
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        shifted_date = datetime(year, month, day) + td(days=day_offset)
        return f">= DATE({shifted_date.year}, {shifted_date.month}, {shifted_date.day})"
    
    def shift_end(match):
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        shifted_date = datetime(year, month, day) + td(days=day_offset)
        return f"< DATE({shifted_date.year}, {shifted_date.month}, {shifted_date.day})"
    
    for event in shifted.get("events", []):
        if event.get("name") == "Execute DAX Query":
            query_text = event.get("metrics", {}).get("QueryText", "")
            if query_text:
                query_text = re.sub(START_PATTERN, shift_start, query_text)
                query_text = re.sub(END_PATTERN, shift_end, query_text)
                event["metrics"]["QueryText"] = query_text
    return shifted


def clear_aas_cache(model_name: str, workspace_name: str) -> tuple:
    """Clear AAS engine cache using XMLA ClearCache (SYNCHRONOUS)"""
    try:
        datasets = fabric.list_datasets(workspace=workspace_name)
        dataset_row = datasets[datasets['Dataset Name'] == model_name]
        if len(dataset_row) == 0:
            return False, f"Dataset '{model_name}' not found"
        dataset_id = dataset_row["Dataset ID"].values[0]
        xmla_cmd = f"""
            <ClearCache xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">  
                <Object><DatabaseID>{dataset_id}</DatabaseID></Object>  
            </ClearCache>
        """
        fabric.execute_xmla(model_name, xmla_command=xmla_cmd, workspace=workspace_name)
        return True, "Cache cleared"
    except Exception as e:
        return False, f"Failed: {str(e)}"


def refresh_fabric_dataset(model_name: str, workspace_name: str, refresh_type: str = "full") -> tuple:
    """Trigger dataset refresh via Fabric API (ASYNCHRONOUS - returns immediately)"""
    try:
        fabric.refresh_dataset(dataset=model_name, workspace=workspace_name, refresh_type=refresh_type)
        return True, f"Refresh triggered ({refresh_type})"
    except Exception as e:
        return False, f"Failed: {str(e)}"


def compute_session_stats(session_log_folder: str, num_iterations: int) -> dict:
    """Read ALL CSVs from ALL iterations and compute SESSION-level stats."""
    all_durations = []
    files_read = 0
    
    for iter_num in range(1, num_iterations + 1):
        iter_folder = f"{session_log_folder}_iter{iter_num}"
        csv_files = glob.glob(f"{iter_folder}/*.csv")
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                for col in ['duration_ms', 'duration', 'elapsed_ms', 'elapsed', 'query_duration_ms']:
                    if col in df.columns:
                        durations = df[col].dropna().tolist()
                        all_durations.extend(durations)
                        files_read += 1
                        break
            except Exception as e:
                print(f"  Warning: Could not read {csv_file}: {e}")
    
    if not all_durations:
        return {"files_read": files_read, "query_count": 0, "avg_ms": None, "p50_ms": None, "p90_ms": None, "p95_ms": None, "p99_ms": None}
    
    arr = np.array(all_durations)
    return {
        "files_read": files_read,
        "query_count": len(all_durations),
        "avg_ms": round(np.mean(arr), 2),
        "p50_ms": round(np.percentile(arr, 50), 2),
        "p90_ms": round(np.percentile(arr, 90), 2),
        "p95_ms": round(np.percentile(arr, 95), 2),
        "p99_ms": round(np.percentile(arr, 99), 2)
    }


# ========== SESSION START ==========
session_start_time = datetime.now()
session_log_folder = f"/lakehouse/default/Files/test/PerfScenarios/logs/{loadtestId}"

print("=" * 70)
print(f"SESSION: {loadtestId}")
print(f"Test Label: {test_label}")
print(f"Started: {session_start_time.isoformat()}")
print(f"Concurrent Users: {num_concurrent_users} | Iterations: {num_iterations}")
print(f"Clear cache per iteration: {clear_cache_per_iter}")
print(f"Fabric refresh per iteration: {refresh_fabric_per_iter}")
print("=" * 70)

# Store per-iteration timing data
iteration_records = []

# ========== ITERATION LOOP ==========
for iter_num in range(1, num_iterations + 1):
    day_offset = iter_num - 1
    iter_loadtestId = f"{loadtestId}_iter{iter_num}"
    
    print(f"\n{'─' * 70}")
    print(f"ITERATION {iter_num}/{num_iterations}")
    print(f"{'─' * 70}")
    
    # Record iteration start
    iter_start_time = datetime.now()
    print(f"[1/5] Started: {iter_start_time.strftime('%H:%M:%S')}")
    
    # Fabric refresh (async - triggers reload from source)
    if refresh_fabric_per_iter:
        print(f"[2/5] Triggering Fabric refresh...")
        success, msg = refresh_fabric_dataset(dataset, workspace)
        print(f"      {msg}")
    else:
        print(f"[2/5] Fabric refresh: SKIPPED")
    
    # Clear cache (sync - clears engine cache)
    if clear_cache_per_iter:
        print(f"[3/5] Clearing AAS cache...")
        success, msg = clear_aas_cache(dataset, workspace)
        print(f"      {msg}")
    else:
        print(f"[3/5] Cache clear: SKIPPED")
    
    # Shift dates
    print(f"[4/5] Shifting dates +{day_offset} days...")
    iter_runtime = shift_dates_in_runtime_json(data, day_offset)
    iter_runtime_filename = f"runtime_{loadtestId}_iter{iter_num}.json"
    iter_runtime_path = f"/lakehouse/default/Files/test/PerfScenarios/RunTime/{iter_runtime_filename}"
    with open(iter_runtime_path, 'w') as f:
        json.dump(iter_runtime, f, indent=2)
    
    # Build and launch DAG
    print(f"[5/5] Launching DAG ({num_concurrent_users} users)...")
    DAG = {"activities": [], "concurrency": num_concurrent_users}
    
    for thread_id in range(1, num_concurrent_users + 1):
        thread_args = base_args.copy()
        thread_args["threadId"] = thread_id
        thread_args["loadtestId"] = iter_loadtestId
        thread_args["iterations"] = 1
        thread_args["perf_analyzer_filename"] = iter_runtime_path
        thread_args["iteration_number"] = iter_num
        thread_args["date_offset_days"] = day_offset
        
        DAG["activities"].append({
            "name": f"iter{iter_num}_user{thread_id}",
            "path": "RunPerfScenario_Parallel",
            "args": thread_args,
            "timeoutPerCellInSeconds": 300  # 5 minutes per cell
        })
    
    dag_start = time.time()
    try:
        notebookutils.notebook.runMultiple(DAG, {"displayDAGVia498WorkAround": True})
        dag_duration = time.time() - dag_start
        dag_status = "SUCCESS"
    except Exception as e:
        dag_duration = time.time() - dag_start
        dag_status = f"FAILED: {str(e)}"
    
    # Record iteration end
    iter_end_time = datetime.now()
    iter_duration = (iter_end_time - iter_start_time).total_seconds()
    
    print(f"      DAG: {dag_status} ({dag_duration:.2f}s)")
    print(f"      Iteration ended: {iter_end_time.strftime('%H:%M:%S')} (duration: {iter_duration:.2f}s)")
    
    # Store iteration record
    iteration_records.append({
        "iteration": iter_num,
        "start_time": iter_start_time.isoformat(),
        "end_time": iter_end_time.isoformat(),
        "duration_sec": round(iter_duration, 2),
        "date_offset_days": day_offset,
        "dag_status": dag_status,
        "dag_duration_sec": round(dag_duration, 2),
        "fabric_refresh": refresh_fabric_per_iter,
        "cache_cleared": clear_cache_per_iter
    })
    
    # Brief pause between iterations
    if iter_num < num_iterations:
        time.sleep(3)

# ========== SESSION COMPLETE - COMPUTE STATS ==========
session_end_time = datetime.now()
session_duration = (session_end_time - session_start_time).total_seconds()

print(f"\n{'=' * 70}")
print(f"ALL ITERATIONS COMPLETE - Computing session stats...")
print(f"{'=' * 70}")

session_stats = compute_session_stats(session_log_folder, num_iterations)
print(f"Files read: {session_stats['files_read']}")
print(f"Total queries: {session_stats['query_count']}")
if session_stats['avg_ms']:
    print(f"")
    print(f"SESSION STATS (aggregated from all {num_iterations} iterations):")
    print(f"  avg  = {session_stats['avg_ms']} ms")
    print(f"  p50  = {session_stats['p50_ms']} ms")
    print(f"  p90  = {session_stats['p90_ms']} ms")
    print(f"  p95  = {session_stats['p95_ms']} ms")
    print(f"  p99  = {session_stats['p99_ms']} ms")

# ========== SAVE TELEMETRY ==========
telemetry = {
    "session_id": loadtestId,
    "test_label": test_label,
    "session_start_time": session_start_time.isoformat(),
    "session_end_time": session_end_time.isoformat(),
    "session_duration_sec": round(session_duration, 2),
    "concurrent_users": num_concurrent_users,
    "num_iterations": num_iterations,
    "cache_cleared_per_iteration": clear_cache_per_iter,
    "fabric_refresh_per_iteration": refresh_fabric_per_iter,
    "iterations": iteration_records,
    "session_stats": {
        "query_count": session_stats['query_count'],
        "avg_ms": session_stats['avg_ms'],
        "p50_ms": session_stats['p50_ms'],
        "p90_ms": session_stats['p90_ms'],
        "p95_ms": session_stats['p95_ms'],
        "p99_ms": session_stats['p99_ms']
    }
}

telemetry_path = f"{session_log_folder}/session_telemetry.json"
try:
    os.makedirs(session_log_folder, exist_ok=True)
    with open(telemetry_path, 'w') as f:
        json.dump(telemetry, f, indent=2)
    print(f"\nTelemetry saved: {telemetry_path}")
except Exception as e:
    print(f"Failed to save telemetry: {e}")

# Print summary
print(f"\n{'=' * 70}")
print(f"SESSION SUMMARY: {loadtestId}")
print(f"Test Label: {test_label}")
print(f"{'=' * 70}")
print(f"Duration: {session_duration:.2f}s ({session_start_time.strftime('%H:%M:%S')} - {session_end_time.strftime('%H:%M:%S')})")
print(f"Fabric Refresh: {refresh_fabric_per_iter} | Cache Clear: {clear_cache_per_iter}")
print(f"")
print(f"Iterations:")
for rec in iteration_records:
    start_short = rec['start_time'][11:19]
    end_short = rec['end_time'][11:19]
    print(f"  {rec['iteration']}: {start_short} - {end_short} ({rec['duration_sec']}s) [{rec['dag_status']}]")
print(f"")
print(f"Session Stats: avg={session_stats['avg_ms']}ms, p50={session_stats['p50_ms']}ms, p90={session_stats['p90_ms']}ms, p95={session_stats['p95_ms']}ms, p99={session_stats['p99_ms']}ms")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Analyze Power BI Trace - Visual Container Lifecycle Baseline
# Uses ORIGINAL trace file for accurate baseline timing

# Use original file for baseline (not parameterized)
baseline_file = "/lakehouse/default/Files/test/PerfScenarios/Queries/PowerBIPerformanceData_Parameterized_New.json"

try:
    with open(baseline_file, 'r', encoding='utf-8-sig') as f:
        trace_data = json.load(f)
    
    events = trace_data.get('events', [])
    visual_lifecycle = [e for e in events if e.get('name') == 'Visual Container Lifecycle']
    
    # Find common start time (all visuals start together)
    start_times = [dt.fromisoformat(v.get('start', '').replace('Z', '+00:00')) for v in visual_lifecycle]
    common_start = min(start_times)
    
    print(f"Baseline: {baseline_file.split('/')[-1]}")
    print(f"Visuals: {len(visual_lifecycle)} | Parallel start: {common_start.strftime('%H:%M:%S')}")
    print("-" * 90)
    print(f"{'#':<3} {'Visual':<28} {'Type':<22} {'Complete(ms)':<12} {'DAX(ms)':<10} {'DAX'}")
    print("-" * 90)
    
    visual_baselines = []
    for v in visual_lifecycle:
        end_dt = dt.fromisoformat(v.get('end', '').replace('Z', '+00:00'))
        completion_ms = (end_dt - common_start).total_seconds() * 1000
        
        visual_title = v.get('metrics', {}).get('visualTitle', 'Unknown')
        visual_type = v.get('metrics', {}).get('visualType', 'Unknown')
        visual_id = v.get('id')
        
        # Trace hierarchy: Visual -> Query -> Execute Semantic Query -> Execute DAX Query
        has_dax, dax_duration_ms = False, 0
        for q in events:
            if q.get('name') == 'Query' and q.get('parentId') == visual_id:
                for sq in events:
                    if sq.get('name') == 'Execute Semantic Query' and sq.get('parentId') == q.get('id'):
                        for dax in events:
                            if dax.get('name') == 'Execute DAX Query' and dax.get('parentId') == sq.get('id'):
                                has_dax = True
                                dax_start = dt.fromisoformat(dax.get('start', '').replace('Z', '+00:00'))
                                dax_end = dt.fromisoformat(dax.get('end', '').replace('Z', '+00:00'))
                                dax_duration_ms = (dax_end - dax_start).total_seconds() * 1000
                                break
        
        visual_baselines.append({
            'visual_title': visual_title,
            'visual_type': visual_type,
            'completion_ms': round(completion_ms, 1),
            'dax_ms': round(dax_duration_ms, 1),
            'has_dax': has_dax
        })
    
    visual_baselines.sort(key=lambda x: x['completion_ms'])
    
    for idx, v in enumerate(visual_baselines, 1):
        dax_str = f"{v['dax_ms']:.0f}" if v['has_dax'] else "-"
        dax_marker = "Y" if v['has_dax'] else "-"
        print(f"{idx:<3} {v['visual_title']:<28} {v['visual_type']:<22} {v['completion_ms']:<12.0f} {dax_str:<10} {dax_marker}")
    
    dax_visuals = [v for v in visual_baselines if v['has_dax']]
    baseline_page_load = max(v['completion_ms'] for v in visual_baselines)
    
    print("-" * 90)
    print(f"Total: {len(visual_baselines)} visuals | DAX: {len(dax_visuals)} | Page Load: {baseline_page_load:.0f}ms ({baseline_page_load/1000:.2f}s)")
    
    # Verify hierarchy tracing worked
    print(f"\nHierarchy verification: {len(dax_visuals)} visuals mapped to DAX queries")
    baseline_df_data = visual_baselines

except FileNotFoundError:
    print(f"Error: {baseline_file} not found")
    print("Upload PowerBIPerformanceData.json to /lakehouse/default/Files/test/PerfScenarios/Queries/")
    baseline_df_data, baseline_page_load = [], 0
except Exception as e:
    print(f"Error: {e}")
    baseline_df_data, baseline_page_load = [], 0

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Consolidate Results

df_list = []
print(f"Session: {loadtestId} | Iterations: {num_iterations}")
print("-" * 60)

base_log_path = "/lakehouse/default/Files/test/PerfScenarios/logs"
csv_files_all = []

# Find all iteration folders for this session
for iter_num in range(1, num_iterations + 1):
    iter_folder = f"{base_log_path}/{loadtestId}_iter{iter_num}"
    try:
        iter_files = [f for f in os.listdir(iter_folder) if f.endswith('.csv')]
        for f in iter_files:
            csv_files_all.append((iter_folder, f, iter_num))
    except FileNotFoundError:
        print(f"  [WARN] Folder not found: {iter_folder}")

print(f"Total CSV files found: {len(csv_files_all)}")

for (iter_folder, filename, iter_num) in csv_files_all:
    file_path = os.path.join(iter_folder, filename)
    polars_df = pl.read_csv(file_path)
    
    # ADD iteration_number column if not present
    if 'iteration_number' not in polars_df.columns:
        polars_df = polars_df.with_columns(pl.lit(iter_num).alias('iteration_number'))
    
    # Use epoch seconds to create datetime columns
    polars_df = polars_df.with_columns([
        pl.from_epoch(pl.col("start_time"), time_unit="s").dt.truncate("1s").dt.replace_time_zone("UTC").alias("start_time_s"),
        pl.from_epoch(pl.col("start_time"), time_unit="s").dt.replace_time_zone("UTC").alias("start_time_dt")
    ])
    
    df_list.append(polars_df)

if df_list:
    combined_df = pl.concat(df_list)
    print(f"Combined {len(df_list)} CSV files, {len(combined_df)} total records")
    
    # Show breakdown summary
    if 'thread_id' in combined_df.columns:
        thread_counts = combined_df.group_by("thread_id").agg(pl.len().alias("count")).sort("thread_id")
        print(f"Sessions: {len(thread_counts)} | ", end="")
    if 'iteration_number' in combined_df.columns:
        iter_counts = combined_df.group_by("iteration_number").agg(pl.len().alias("count")).sort("iteration_number")
        print(f"Iterations: {len(iter_counts)} | Queries/iter: {iter_counts['count'][0]}")
    print(f"Columns: {combined_df.columns}")
else:
    print("\nNo CSV files found in any iteration folder")
    combined_df = None

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Results Analysis - Compare with Power BI Baseline

if combined_df is not None:
    combined_df = combined_df.with_columns(
        pl.col("start_time_s").cast(pl.Datetime).alias("start_time_s_dt")
    )
    
    # Calculate completion time from common start (mimics Power BI parallel rendering)
    min_start = combined_df.select(pl.col("start_time").min())[0, 0]
    max_end = combined_df.select((pl.col("start_time") + pl.col("duration")).max())[0, 0]
    
    combined_df = combined_df.with_columns([
        ((pl.col("start_time") - min_start) * 1000).alias("offset_ms"),
        ((pl.col("start_time") - min_start) + pl.col("duration")).alias("completion_time")
    ])
    
    # Convert epoch to datetime
    from datetime import datetime as dt
    start_utc = dt.fromtimestamp(min_start, tz=timezone.utc)
    end_utc = dt.fromtimestamp(max_end, tz=timezone.utc)
    pst = timezone(td(hours=-8))
    start_pst = start_utc.astimezone(pst)
    end_pst = end_utc.astimezone(pst)
    
    # Aggregate by query_number (all iterations combined) - for Fabric Avg column
    query_stats_avg = combined_df.group_by("query_number").agg([
        pl.col("duration").mean().alias("avg_duration_s"),
        pl.col("visual_name").first().alias("visual_name"),
    ]).sort("query_number")
    
    stats = combined_df.select([
        pl.col("duration").min().alias("min"),
        pl.col("duration").max().alias("max"),
        pl.col("duration").mean().alias("avg"),
        pl.col("duration").quantile(0.50, interpolation="linear").alias("p50"),
        pl.col("duration").quantile(0.90, interpolation="linear").alias("p90"),
        pl.col("duration").quantile(0.95, interpolation="linear").alias("p95"),
        pl.col("duration").quantile(0.99, interpolation="linear").alias("p99"),
        pl.col("completion_time").max().alias("page_load"),
        pl.len().alias("count")
    ])
    
    fabric_page_load = stats['page_load'][0] * 1000
    total_duration_s = max_end - min_start
    
    print("=" * 120)
    print("LOAD TEST RESULTS")
    print("=" * 120)
    print(f"Execution: {start_pst.strftime('%Y-%m-%d %H:%M:%S')} - {end_pst.strftime('%H:%M:%S')} PST ({total_duration_s:.1f}s)")
    print(f"Query Stats ({stats['count'][0]} queries): min={stats['min'][0]*1000:.0f}ms, avg={stats['avg'][0]*1000:.0f}ms, p50={stats['p50'][0]*1000:.0f}ms, p90={stats['p90'][0]*1000:.0f}ms, p95={stats['p95'][0]*1000:.0f}ms, p99={stats['p99'][0]*1000:.0f}ms")
    
    # ========== PER-ITERATION PERFORMANCE ANALYSIS ==========
    print("\n" + "=" * 120)
    print("PER-ITERATION PERFORMANCE ANALYSIS")
    print("=" * 120)
    
    if 'iteration_number' in combined_df.columns:
        iter_analysis = combined_df.group_by("iteration_number").agg([
            pl.col("duration").mean().alias("avg_s"),
            pl.col("duration").quantile(0.50, interpolation="linear").alias("p50_s"),
            pl.col("duration").quantile(0.90, interpolation="linear").alias("p90_s"),
            pl.col("duration").quantile(0.95, interpolation="linear").alias("p95_s"),
            pl.col("duration").quantile(0.99, interpolation="linear").alias("p99_s"),
            ((pl.col("start_time") + pl.col("duration")).max() - pl.col("start_time").min()).alias("page_load_s"),
            pl.len().alias("query_count")
        ]).sort("iteration_number")
        
        # Convert to ms
        iter_analysis = iter_analysis.with_columns([
            (pl.col("avg_s") * 1000).round(0).alias("avg_ms"),
            (pl.col("p50_s") * 1000).round(0).alias("p50_ms"),
            (pl.col("p90_s") * 1000).round(0).alias("p90_ms"),
            (pl.col("p95_s") * 1000).round(0).alias("p95_ms"),
            (pl.col("p99_s") * 1000).round(0).alias("p99_ms"),
            (pl.col("page_load_s") * 1000).round(0).alias("page_load_ms")
        ]).select(["iteration_number", "query_count", "avg_ms", "p50_ms", "p90_ms", "p95_ms", "p99_ms", "page_load_ms"])
        
        print("\nPer-Iteration Stats Table:")
        print(iter_analysis)
    else:
        print("\n[WARN] 'iteration_number' column not found")
    
    # ========== PER-ITERATION POWER BI vs FABRIC COMPARISON ==========
    if baseline_df_data and 'iteration_number' in combined_df.columns:
        dax_visuals = [v for v in baseline_df_data if v['has_dax']]
        non_dax_visuals = [v for v in baseline_df_data if not v['has_dax']]
        pbi_page_load = baseline_page_load
        
        # Calculate overall Fabric avg page load
        fabric_avg_page_load = sum(iter_analysis['page_load_ms'].to_list()) / len(iter_analysis)
        
        unique_iters = sorted(combined_df['iteration_number'].unique().to_list())
        
        for iter_num in unique_iters:
            iter_df = combined_df.filter(pl.col('iteration_number') == iter_num)
            
            # Get per-query stats for this iteration
            iter_query_stats = iter_df.group_by("query_number").agg([
                pl.col("duration").mean().alias("avg_duration_s"),
                pl.col("visual_name").first().alias("visual_name"),
            ]).sort("query_number")
            
            # Calculate page load for this iteration
            iter_min_start = iter_df.select(pl.col("start_time").min())[0, 0]
            iter_max_end = iter_df.select((pl.col("start_time") + pl.col("duration")).max())[0, 0]
            iter_page_load_ms = (iter_max_end - iter_min_start) * 1000
            
            print("\n" + "=" * 120)
            print(f"POWER BI vs FABRIC COMPARISON - ITERATION {iter_num}")
            print("=" * 120)
            print(f"\n{'#':<3} {'Visual':<28} {'Type':<18} {'PBI(ms)':<10} {'Fabric(ms)':<12} {'Fabric Avg':<12} {'Diff vs PBI':<16} {'Notes'}")
            print("-" * 120)
            
            row_num = 1
            
            # DAX visuals - have Fabric comparison
            for idx, visual in enumerate(dax_visuals):
                if idx < len(iter_query_stats):
                    fabric_ms = iter_query_stats['avg_duration_s'][idx] * 1000
                    fabric_avg_ms = query_stats_avg['avg_duration_s'][idx] * 1000
                    diff_ms = fabric_ms - visual['dax_ms']
                    diff_pct = ((fabric_ms / visual['dax_ms']) - 1) * 100 if visual['dax_ms'] > 0 else 0
                    diff_str = f"{diff_ms:+.0f}ms ({diff_pct:+.1f}%)"
                    print(f"{row_num:<3} {visual['visual_title']:<28} {visual['visual_type']:<18} {visual['dax_ms']:<10.0f} {fabric_ms:<12.0f} {fabric_avg_ms:<12.0f} {diff_str:<16} DAX Query")
                row_num += 1
            
            # Non-DAX visuals - render-only
            for visual in non_dax_visuals:
                print(f"{row_num:<3} {visual['visual_title']:<28} {visual['visual_type']:<18} {visual['completion_ms']:<10.0f} {'N/A':<12} {'N/A':<12} {'-':<16} Render-only")
                row_num += 1
            
            diff_page = iter_page_load_ms - pbi_page_load
            diff_pct_page = ((iter_page_load_ms / pbi_page_load) - 1) * 100 if pbi_page_load > 0 else 0
            
            print("-" * 120)
            print(f"Page Load: PBI {pbi_page_load:.0f}ms | Iter {iter_num}: {iter_page_load_ms:.0f}ms | Fabric Avg: {fabric_avg_page_load:.0f}ms | Diff vs PBI: {diff_page:+.0f}ms ({diff_pct_page:+.1f}%)")
        
        print(f"\nSummary: {len(dax_visuals)} DAX queries executed | {len(non_dax_visuals)} render-only visuals (client-side, not load-testable)")
    
    # ========== PER-SESSION STATS ==========
    print("\n" + "=" * 120)
    print("PER-SESSION STATS")
    print("=" * 120)
    session_stats_df = combined_df.group_by("thread_id").agg([
        pl.col("duration").mean().alias("avg_ms"),
        pl.col("duration").quantile(0.50, interpolation="linear").alias("p50_ms"),
        pl.col("duration").quantile(0.90, interpolation="linear").alias("p90_ms"),
        pl.col("duration").quantile(0.95, interpolation="linear").alias("p95_ms"),
        pl.col("completion_time").max().alias("page_load_s"),
        pl.len().alias("query_count")
    ]).sort("thread_id")
    
    # Convert to ms for display
    session_stats_df = session_stats_df.with_columns([
        (pl.col("avg_ms") * 1000).round(0).alias("avg_ms"),
        (pl.col("p50_ms") * 1000).round(0).alias("p50_ms"),
        (pl.col("p90_ms") * 1000).round(0).alias("p90_ms"),
        (pl.col("p95_ms") * 1000).round(0).alias("p95_ms"),
        (pl.col("page_load_s") * 1000).round(0).alias("page_load_ms")
    ]).select(["thread_id", "query_count", "avg_ms", "p50_ms", "p90_ms", "p95_ms", "page_load_ms"])
    print(session_stats_df)
    
    print("\n" + "=" * 120)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# DAX Query Calculated Results - Execute queries and compare across iterations
import json
import re
import pandas as pd
import numpy as np

def is_percentage_column(col_name):
    """Check if column should be formatted as percentage"""
    pct_keywords = ['rate', 'percent', 'pct', 'ratio', '%', 'approval', 'decline', 'auth']
    return any(kw in col_name.lower() for kw in pct_keywords)

def format_value(v, col_name=None):
    """Format a single value for display"""
    if pd.isna(v):
        return ""
    # Convert to float if it's any numeric type
    try:
        num_val = float(v)
    except (ValueError, TypeError):
        return str(v)[:60]
    
    # Only treat as percentage if value is in 0-1 range AND column suggests percentage
    # OR if value is small decimal (0-1 range) regardless of column name
    is_pct_column = col_name and is_percentage_column(col_name)
    is_small_decimal = 0 <= abs(num_val) <= 1
    
    if is_small_decimal and (is_pct_column or 0 < abs(num_val) < 1):
        return f"{num_val*100:.2f}%"
    # Large numbers - no decimals
    elif abs(num_val) >= 1_000_000:
        return f"{num_val:,.0f}"
    # Whole numbers - no decimals
    elif num_val == int(num_val):
        return f"{int(num_val):,}"
    # Regular decimals - 2 decimal places max
    else:
        return f"{num_val:,.2f}"
    return str(v)[:60]

def format_dataframe_for_display(df):
    """Create a new DataFrame with formatted string values for display"""
    return pd.DataFrame({col: [format_value(v, col) for v in df[col]] for col in df.columns})

skip_visuals = ['Date', 'Button', 'Slicer', 'Period Type']
all_iteration_results = {}

# ========== EXECUTE DAX FOR EACH ITERATION ==========
for iter_num in range(1, num_iterations + 1):
    iter_runtime_path = f"/lakehouse/default/Files/test/PerfScenarios/RunTime/runtime_{loadtestId}_iter{iter_num}.json"
    
    print(f"\n{'=' * 110}")
    print(f"ITERATION {iter_num} - DAX QUERY RESULTS (Date Offset: +{iter_num - 1} days)")
    print(f"{'=' * 110}")
    
    try:
        with open(iter_runtime_path, 'r', encoding='utf-8-sig') as f:
            iter_trace_data = json.load(f)
    except FileNotFoundError:
        if iter_num == 1:
            with open(query_file, 'r', encoding='utf-8-sig') as f:
                iter_trace_data = json.load(f)
        else:
            print(f"  [WARN] Runtime file not found: {iter_runtime_path}")
            continue
    
    events = iter_trace_data.get('events', [])
    
    # Build visual map
    visual_map = {e.get('id'): e.get('metrics', {}).get('visualTitle', 'Unknown') 
                  for e in events if e.get('name') == 'Visual Container Lifecycle'}
    
    # Extract DAX queries with visual names
    dax_queries = []
    for event in events:
        if event.get('name') == 'Execute DAX Query':
            query_text = event.get('metrics', {}).get('QueryText', '')
            if query_text:
                visual_name = "Unknown"
                parent_id = event.get('parentId')
                for e in events:
                    if e.get('id') == parent_id and e.get('name') == 'Execute Semantic Query':
                        for q in events:
                            if q.get('id') == e.get('parentId') and q.get('name') == 'Query':
                                visual_name = visual_map.get(q.get('parentId'), 'Unknown')
                                break
                        break
                dax_queries.append({'visual': visual_name, 'query': query_text})
    
    # Show date range
    if dax_queries:
        first_query = dax_queries[0]['query']
        start_m = re.search(r'>=\s*DATE\s*\(\s*(\d{4})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})\s*\)', first_query)
        end_m = re.search(r'<\s*DATE\s*\(\s*(\d{4})\s*,\s*(\d{1,2})\s*,\s*(\d{1,2})\s*\)', first_query)
        if start_m and end_m:
            print(f"Date Range: {start_m.group(1)}-{start_m.group(2).zfill(2)}-{start_m.group(3).zfill(2)} to {end_m.group(1)}-{end_m.group(2).zfill(2)}-{end_m.group(3).zfill(2)}")
    
    print(f"\nExecuting {len(dax_queries)} DAX Queries...")
    print("-" * 110)
    print(f"{'#':<3} {'Visual':<30} {'Result Summary':<60} {'Status'}")
    print("-" * 110)
    
    query_results = []
    for idx, dq in enumerate(dax_queries, 1):
        try:
            result_df = fabric.evaluate_dax(dataset=dataset, workspace=workspace, dax_string=dq['query'])
            # Build summary string
            if len(result_df) == 0:
                summary = "Empty result"
            elif len(result_df) == 1 and len(result_df.columns) == 1:
                summary = format_value(result_df.iloc[0, 0])
            elif len(result_df) == 1:
                vals = [format_value(result_df.iloc[0][c], c) for c in list(result_df.columns)[:3]]
                summary = " | ".join(vals) + (f" (+{len(result_df.columns)-3} cols)" if len(result_df.columns) > 3 else "")
            else:
                summary = f"{len(result_df)} rows × {len(result_df.columns)} cols (first: {format_value(result_df.iloc[0, 0])})"
            query_results.append({'query_num': idx, 'visual': dq['visual'], 'result_df': result_df,
                                  'summary': summary, 'status': 'success', 'row_count': len(result_df), 'col_count': len(result_df.columns)})
        except Exception as e:
            summary = str(e)[:60]
            query_results.append({'query_num': idx, 'visual': dq['visual'], 'result_df': None,
                                  'summary': summary, 'status': 'error', 'row_count': 0, 'col_count': 0})
        print(f"{idx:<3} {dq['visual'][:30]:<30} {summary:<60} {'✓' if query_results[-1]['status'] == 'success' else '✗'}")
    
    print("-" * 110)
    success_count = len([r for r in query_results if r['status'] == 'success'])
    print(f"Executed: {len(dax_queries)} | Success: {success_count} | Failed: {len(dax_queries) - success_count}")
    all_iteration_results[iter_num] = query_results
    
    # Show detailed results
    print(f"\n--- DETAILED RESULTS (Iteration {iter_num}) ---")
    for qr in query_results:
        if qr['status'] == 'success' and qr['result_df'] is not None:
            if any(skip in qr['visual'] for skip in skip_visuals):
                continue
            df = qr['result_df']
            is_matrix = 'Matrix' in qr['visual'] or (len(df) > 1 and len(df.columns) > 2)
            if is_matrix:
                print(f"\nQuery {qr['query_num']}: {qr['visual']} (Matrix - {len(df)} rows × {len(df.columns)} cols)")
                print("-" * 80)
                display(format_dataframe_for_display(df))
            elif len(df) <= 10:
                print(f"\nQuery {qr['query_num']}: {qr['visual']}")
                print("-" * 60)
                display(format_dataframe_for_display(df))

# ========== CROSS-ITERATION COMPARISON ==========
if len(all_iteration_results) > 1:
    print("\n" + "=" * 110)
    print("CROSS-ITERATION COMPARISON SUMMARY")
    print("=" * 110)
    print("\nNote: Different date ranges may produce different metric values")
    print("-" * 110)
    print(f"{'Visual':<35}" + "".join(f"{'Iter ' + str(i):<20}" for i in sorted(all_iteration_results.keys())))
    print("-" * 110)
    
    for qr in all_iteration_results[1]:
        if qr['status'] == 'success' and qr['row_count'] == 1 and qr['col_count'] == 1:
            print(f"{qr['visual'][:35]:<35}", end="")
            for iter_num in sorted(all_iteration_results.keys()):
                match = [r for r in all_iteration_results[iter_num] if r['visual'] == qr['visual'] and r['status'] == 'success']
                val_str = format_value(match[0]['result_df'].iloc[0, 0]) if match and match[0]['result_df'] is not None else "N/A"
                print(f"{val_str:<20}", end="")
            print()
    print("=" * 110)

print("\n" + "=" * 110)
print("DAX QUERY EXECUTION COMPLETE")
print("=" * 110)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }

# CELL ********************

# Export Results to Lakehouse
import json
import os

end_date_str = datetime.now().strftime("%Y-%m-%d")
results_folder = f"/lakehouse/default/Files/test/PerfScenarios/results/{end_date_str}/{loadtestId}"
results_folder_relative = f"Files/test/PerfScenarios/results/{end_date_str}/{loadtestId}"

if combined_df is not None:
    notebookutils.fs.mkdirs(results_folder_relative)
    
    # 1. Export raw results CSV (add test_label column)
    csv_path = f"{results_folder}/results.csv"
    results_pdf = combined_df.to_pandas()
    results_pdf['test_label'] = test_label
    results_pdf.to_csv(csv_path, index=False)
    # combined_df.to_pandas().to_csv(csv_path, index=False)
    
    # 2. Build summary statistics
    query_summary_stats = combined_df.group_by("query_number", "visual_name").agg([
        pl.col("duration").min().alias("min_s"), pl.col("duration").max().alias("max_s"),
        pl.col("duration").mean().alias("avg_s"), pl.col("duration").quantile(0.50).alias("p50_s"),
        pl.col("duration").quantile(0.90).alias("p90_s"), pl.col("duration").quantile(0.95).alias("p95_s"),
        pl.col("duration").quantile(0.99).alias("p99_s"), pl.len().alias("execution_count")
    ]).sort("query_number")
    
    summary_rows = [{
        'test_label': test_label, 
        'query_number': row['query_number'], 'visual': row['visual_name'],
        'start_date': str(start_date), 'end_date': str(end_date), 'period_type': period_type,
        'min_ms': round(row['min_s'] * 1000, 2), 'max_ms': round(row['max_s'] * 1000, 2),
        'avg_ms': round(row['avg_s'] * 1000, 2), 'p50_ms': round(row['p50_s'] * 1000, 2),
        'p90_ms': round(row['p90_s'] * 1000, 2), 'p95_ms': round(row['p95_s'] * 1000, 2),
        'p99_ms': round(row['p99_s'] * 1000, 2), 'execution_count': row['execution_count']
    } for row in query_summary_stats.iter_rows(named=True)]
    
    # Add overall summary
    overall_stats = combined_df.select([
        pl.col("duration").min().alias("min"), pl.col("duration").max().alias("max"),
        pl.col("duration").mean().alias("avg"), pl.col("duration").quantile(0.50).alias("p50"),
        pl.col("duration").quantile(0.90).alias("p90"), pl.col("duration").quantile(0.95).alias("p95"),
        pl.col("duration").quantile(0.99).alias("p99"), pl.len().alias("count")
    ])
    summary_rows.append({
        'test_label': test_label,
        'query_number': 'ALL', 'visual': 'OVERALL', 'start_date': str(start_date), 'end_date': str(end_date),
        'period_type': period_type, 'min_ms': round(overall_stats['min'][0] * 1000, 2),
        'max_ms': round(overall_stats['max'][0] * 1000, 2), 'avg_ms': round(overall_stats['avg'][0] * 1000, 2),
        'p50_ms': round(overall_stats['p50'][0] * 1000, 2), 'p90_ms': round(overall_stats['p90'][0] * 1000, 2),
        'p95_ms': round(overall_stats['p95'][0] * 1000, 2), 'p99_ms': round(overall_stats['p99'][0] * 1000, 2),
        'execution_count': int(overall_stats['count'][0])
    })
    
    summary_df = pd.DataFrame(summary_rows)
    summary_csv_path = f"{results_folder}/summary_stats.csv"
    summary_df.to_csv(summary_csv_path, index=False)
    
    # 3. Build calculated results (reuses format_value from Cell 9)
    calculated_rows = []
    if 'query_results' in dir():
        for qr in query_results:
            if any(skip in qr['visual'] for skip in skip_visuals):
                continue
            if qr['status'] == 'success' and qr['result_df'] is not None:
                df = qr['result_df']
                for row_idx, row in df.iterrows():
                    row_data = {'test_label': test_label,'query_num': qr['query_num'], 'visual': qr['visual'], 'status': qr['status'],
                                'row_index': row_idx + 1, 'total_rows': len(df), 'total_cols': len(df.columns)}
                    for col in df.columns:
                        row_data[col] = format_value(row[col], col)
                    calculated_rows.append(row_data)
            elif qr['status'] == 'error':
                calculated_rows.append({'test_label': test_label,'query_num': qr['query_num'], 'visual': qr['visual'], 'status': qr['status'],
                                        'row_index': 0, 'total_rows': 0, 'total_cols': 0, 'error': qr['summary']})
    
    # 4. Export calculated results
    calc_csv_path = f"{results_folder}/calculated_results.csv"
    if calculated_rows:
        calc_df = pd.DataFrame(calculated_rows)
        calc_df.to_csv(calc_csv_path, index=False)
    
    # 5. Export metadata JSON
    json_summary = {
        "test_label": test_label, "loadtest_id": loadtestId, "model": dataset, "workspace": workspace,
        "concurrent_threads": num_sessions, "iterations": iterations,
        "total_queries": int(overall_stats['count'][0]),
        "query_parameters": {"start_date": str(start_date), "end_date": str(end_date), "period_type": period_type},
        "test_date": end_date_str
    }
    json_path = f"{results_folder}/metadata.json"
    with open(json_path, 'w') as f:
        json.dump(json_summary, f, indent=2, default=str)
    
    print(f"Results exported to Lakehouse:")
    print(f"  Test Label: {test_label}")
    print(f"  1. Raw Results CSV:      {csv_path}")
    print(f"  2. Summary Stats CSV:    {summary_csv_path}")
    print(f"  3. Calculated Results:   {calc_csv_path} ({len(calculated_rows)} rows)")
    print(f"  4. Metadata JSON:        {json_path}")
    print(f"\nQuery Parameters: {start_date} to {end_date}, Period: {period_type}")
    print("\n" + "=" * 100)
    print("SUMMARY STATS PREVIEW")
    print("=" * 100)
    display(summary_df)
    if calculated_rows:
        print("\n" + "=" * 100)
        print("CALCULATED RESULTS PREVIEW")
        print("=" * 100)
        display(calc_df)
else:
    print("No results to export (combined_df is None)")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Send Telemetry to App Insights
if combined_df is not None:
    # Build per-iteration stats for telemetry
    per_iteration_stats = []
    if 'iteration_number' in combined_df.columns:
        for iter_num in sorted(combined_df['iteration_number'].unique().to_list()):
            iter_df = combined_df.filter(pl.col('iteration_number') == iter_num)
            if len(iter_df) > 0:
                iter_s = iter_df.select([
                    pl.col('duration').mean().alias('avg'),
                    pl.col('duration').quantile(0.50).alias('p50'),
                    pl.col('duration').quantile(0.90).alias('p90'),
                    pl.col('duration').quantile(0.95).alias('p95'),
                    pl.col('duration').quantile(0.99).alias('p99'),
                    pl.len().alias('count')
                ])
                per_iteration_stats.append({
                    'iteration': iter_num,
                    'query_count': int(iter_s['count'][0]),
                    'avg_ms': round(iter_s['avg'][0] * 1000, 2),
                    'p50_ms': round(iter_s['p50'][0] * 1000, 2),
                    'p90_ms': round(iter_s['p90'][0] * 1000, 2),
                    'p95_ms': round(iter_s['p95'][0] * 1000, 2),
                    'p99_ms': round(iter_s['p99'][0] * 1000, 2)
                })
    
    result = send_loadtest_telemetry(
        test_label = test_label,
        loadtest_id=loadtestId,
        dataset=dataset,
        workspace=workspace,
        num_sessions=num_sessions,
        iterations=iterations,
        parallel_queries=parallel_queries,
        max_parallel=max_parallel,
        start_date=start_date,
        end_date=end_date,
        period_type=period_type,
        overall_stats=overall_stats,
        combined_df=combined_df,
        summary_rows=summary_rows,
        session_stats=session_stats_df,
        start_utc=start_utc,
        end_utc=end_utc,
        start_pst=start_pst,
        end_pst=end_pst,
        total_duration_s=total_duration_s,
        environment='test',
        # New per-iteration data
        iteration_records=iteration_records if 'iteration_records' in dir() else None,
        per_iteration_stats=per_iteration_stats if per_iteration_stats else None,
        num_iterations=num_iterations if 'num_iterations' in dir() else None
    )
    
    print(f"Telemetry sent to App Insights:")
    print(f"  Test Label: {test_label}")
    print(f"  Events: {result['events_sent']}")
    print(f"  Metrics: {result['metrics_sent']}")
    print(f"  Iteration Timing Events: {result.get('iterations_sent', 0)}")
    print(f"  Iteration Stats Events: {result.get('iteration_stats_sent', 0)}")
    print(f"Test Run ID: {result['test_run_id']}")
    
    # Print per-iteration summary
    if per_iteration_stats:
        print(f"\nPer-Iteration Stats Sent:")
        for s in per_iteration_stats:
            print(f"  Iter {s['iteration']}: avg={s['avg_ms']}ms, p90={s['p90_ms']}ms, p99={s['p99_ms']}ms")
else:
    print("No data to send (combined_df is None)")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
