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

# CELL ********************

# MAGIC %%configure -f
# MAGIC {
# MAGIC    "vCores": 16
# MAGIC }

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# PARAMETERS CELL ********************

# Parameters Cell - Args passed from driver notebook will overwrite these defaults

xmla_endpoint = "powerbi://api.powerbi.com/v1.0/myorg/Payments @ Microsoft [Test]"  # Explicit endpoint
perf_analyzer_filename = "/lakehouse/default/Files/test/PerfScenarios/Queries/PowerBIPerformanceData_Parameterized_New.json"
model = "Payment Analytics Dataset"  # Must match dataset name in workspace
roles = None  # Used with customdata to force active roles. Not needed with effective_username
customdata = None  # customdata for use in RLS without impersonation
effective_username = None  # for RLS with impersonation. Must be the UPN of a user with read+build for the model
iterations = 1  # number of times to run the perf_analyzer_filename in this scenario
delay_sec = 1  # number of seconds to wait between iterations
loadtestId = "localtesting"  # name of load test for logging
threadId = 1  # id of this virtual user to separate logging for multiuser-testing
concurrent_threads = 1  # number of concurrent threads in this test; passed in here only for logging

# Control parallelism within this thread
parallel_queries = True  # Set to False to revert to sequential behavior
max_parallel_queries = 10  # Max queries to run in parallel (None = all queries at once)

# Iteration info (passed from parent)
iteration_number = 1
date_offset_days = 0

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Import Required Libraries
import pandas
from typing import Iterable
import json
import time
import os
import csv
import uuid
import notebookutils  # Fabric notebook utilities
import sempy.fabric as fabric
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from datetime import datetime, timezone
from zoneinfo import ZoneInfo  # Python 3.9+ for timezone handling

# Timezones
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")
UTC_TZ = timezone.utc

# Load CLR for ADOMD
tom = fabric.create_tom_server()
from Microsoft.AnalysisServices.AdomdClient import AdomdConnection

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Thread-safe Connection Pool for Parallel Queries
class ConnectionPool:
    """Manages a pool of ADOMD connections for parallel query execution"""
    def __init__(self, connection_string: str, pool_size: int = 10):
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.connections = []
        self.available = []
        self.lock = Lock()
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Create initial connections"""
        for _ in range(self.pool_size):
            con = AdomdConnection(self.connection_string)
            con.Open()
            self.connections.append(con)
            self.available.append(con)
    
    def get_connection(self) -> AdomdConnection:
        """Get an available connection from the pool"""
        with self.lock:
            if self.available:
                return self.available.pop()
            else:
                # Create a new connection if pool exhausted
                con = AdomdConnection(self.connection_string)
                con.Open()
                self.connections.append(con)
                return con
    
    def return_connection(self, con: AdomdConnection):
        """Return a connection to the pool"""
        with self.lock:
            self.available.append(con)
    
    def close_all(self):
        """Close all connections in the pool"""
        for con in self.connections:
            try:
                con.Close()
            except:
                pass

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Query Execution Functions

def run_query(con: AdomdConnection, query: str) -> int:
    """Execute a DAX query and return row count"""
    cmd = con.CreateCommand()
    cmd.CommandText = query
    rows = 0
    rdr = cmd.ExecuteReader()
    while rdr.Read():
        rows = rows + 1
    rdr.Close()
    return rows


def load_queries(fn: str) -> list:
    """Load queries from PowerBI Performance Analyzer JSON file"""
    queries = []
    with open(fn, encoding='utf-8-sig') as f:
        json_string = f.read()
        d = json.loads(json_string)

        visual_name = ""
        query_text = ""
        for e in d["events"]:
            if e["name"] == "Visual Container Lifecycle":
                visual_name = e["metrics"]["visualTitle"]
                visual_id = e["metrics"]["visualId"]

            if e["name"] == "Execute DAX Query":
                query_text = e["metrics"]["QueryText"]
                queries.append({"visual_name": visual_name, "visual_id": visual_id, "query_text": query_text})
    return queries

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Parallel and Sequential Scenario Runners

def run_single_query(pool: ConnectionPool, q: dict, qn: int, iteration: int) -> dict:
    """Execute a single query and return results - designed for parallel execution"""
    con = pool.get_connection()
    try:
        start = time.time()
        query_text = q["query_text"]
        visual_name = q["visual_name"]
        visual_id = q["visual_id"]
        rows = run_query(con, query_text)
        end = time.time()
        duration = end - start
        
        result = {
            "loadtest_id": loadtestId,
            "model": model,
            "concurrent_threads": concurrent_threads,
            "iterations": iterations,
            "delay_sec": delay_sec,
            "query_number": qn,
            "visual_name": visual_name,
            "visual_id": visual_id,
            "iteration": iteration,
            "query": query_text,
            "rows": rows,
            "duration": duration,
            "start_time": start,  # epoch seconds
            "start_time_utc": datetime.fromtimestamp(start, tz=UTC_TZ),
            "start_time_pacific": datetime.fromtimestamp(start, tz=PACIFIC_TZ),
            "end_time": end,  # epoch seconds
            "end_time_utc": datetime.fromtimestamp(end, tz=UTC_TZ),
            "end_time_pacific": datetime.fromtimestamp(end, tz=PACIFIC_TZ),
            "customdata": customdata,
            "effective_username": effective_username,
            "thread_id": threadId,
            "parallel_execution": True
        }
        return result
    finally:
        pool.return_connection(con)


def run_perf_scenario_parallel(pool: ConnectionPool, queries: list, iteration: int, max_workers: int = None) -> list:
    """Run all queries in PARALLEL within this thread"""
    results = []
    
    if max_workers is None:
        max_workers = len(queries)
    max_workers = min(max_workers, len(queries), pool.pool_size)
    
    print(f"  Running {len(queries)} queries in parallel (max_workers={max_workers})")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_query = {
            executor.submit(run_single_query, pool, q, qn, iteration): qn 
            for qn, q in enumerate(queries, start=1)
        }
        
        for future in as_completed(future_to_query):
            qn = future_to_query[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Query {qn} failed: {e}")
                results.append({
                    "loadtest_id": loadtestId,
                    "query_number": qn,
                    "iteration": iteration,
                    "error": str(e),
                    "duration": 0,
                    "thread_id": threadId
                })
    
    results.sort(key=lambda x: x.get("query_number", 0))
    return results


def run_perf_scenario_sequential(con: AdomdConnection, queries: Iterable[str], i: int) -> list:
    """Original sequential execution - kept for comparison"""
    results = []
    for qn, q in enumerate(queries, start=1):
        start = time.time()
        query_text = q["query_text"]
        visual_name = q["visual_name"]
        visual_id = q["visual_id"]
        rows = run_query(con, query_text)
        end = time.time()
        duration = end - start
        
        result = {
            "loadtest_id": loadtestId,
            "model": model,
            "concurrent_threads": concurrent_threads,
            "iterations": iterations,
            "delay_sec": delay_sec,
            "query_number": qn,
            "visual_name": visual_name,
            "visual_id": visual_id,
            "iteration": i,
            "query": query_text,
            "rows": rows,
            "duration": duration,
            "start_time": start,  # epoch seconds
            "start_time_utc": datetime.fromtimestamp(start, tz=UTC_TZ),
            "start_time_pacific": datetime.fromtimestamp(start, tz=PACIFIC_TZ),
            "end_time": end,  # epoch seconds
            "end_time_utc": datetime.fromtimestamp(end, tz=UTC_TZ),
            "end_time_pacific": datetime.fromtimestamp(end, tz=PACIFIC_TZ),
            "customdata": customdata,
            "effective_username": effective_username,
            "thread_id": threadId,
            "parallel_execution": False
        }
        results.append(result)
        time.sleep(delay_sec)
    return results

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Execute queries and write results
token = notebookutils.credentials.getToken("pbi")

log_folder = f'/lakehouse/default/Files/test/PerfScenarios/logs/{loadtestId}'
try:
    notebookutils.fs.mkdirs(f'Files/test/PerfScenarios/logs/{loadtestId}')
except:
    pass
os.makedirs(log_folder, exist_ok=True)

if xmla_endpoint is None:
    xmla_endpoint = f"powerbi://api.powerbi.com/v1.0/myorg/{notebookutils.runtime.context['currentWorkspaceName']}"

constr = f"Data Source={xmla_endpoint};Initial Catalog={model};password={token};Timeout=7200;"
if effective_username is not None:
    constr += f"EffectiveUserName={effective_username};"
if customdata is not None:
    constr += f"CustomData={customdata};"
if roles is not None:
    constr += f"Roles={roles};"

print(f"Thread {threadId} | Iteration {iteration_number} | +{date_offset_days}d")

try:
    queries = load_queries(perf_analyzer_filename)
    
    if parallel_queries:
        pool_size = min(max_parallel_queries or len(queries), len(queries))
        pool = ConnectionPool(constr, pool_size=pool_size)
        try:
            results = run_perf_scenario_parallel(pool, queries, 0, max_workers=max_parallel_queries)
            for r in results:
                r["iteration_number"] = iteration_number
                r["thread_id"] = threadId
        finally:
            pool.close_all()
    else:
        con = AdomdConnection(constr)
        con.Open()
        try:
            results = run_perf_scenario_sequential(con, queries, 0)
            for r in results:
                r["iteration_number"] = iteration_number
                r["thread_id"] = threadId
        finally:
            con.Close()

    csv_path = f"{log_folder}/{loadtestId}_user_{threadId}.csv"
    if results:
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0].keys()), extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)
        print(f"[OK] {len(results)} queries -> {csv_path}")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    raise


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
