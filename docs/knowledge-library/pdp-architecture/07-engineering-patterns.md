# PDP Engineering Patterns

## Delta Lake Operations

### MERGE/Upsert Pattern
Most Silver and Gold tables use Delta Lake MERGE for idempotent writes:
```python
delta_table.alias("target").merge(
    source_df.alias("source"),
    "target.TransactionId = source.TransactionId"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
```

### Smart Merge (BillingService)
Gold.Billing uses multi-record accumulation:
- **List fields**: Concatenate (e.g., event types accumulated over time)
- **Scalar fields**: MAX/OR logic (take latest non-null value)
- Handles composite keys with multiple source records per entity

### Vacuum and Optimize
- `VACUUM` removes old files (default 7-day retention)
- `OPTIMIZE` compacts small files for read performance
- Z-ORDER on frequently filtered columns (e.g., `ProcessedDate`, `ProviderId`)

### Liquid Clustering (New)
- Replaces traditional partitioning for `gold.payments_journal` and newer tables
- Auto-optimizes data layout based on query patterns
- No manual partition management needed

## Streaming Patterns

### Spark Structured Streaming
```python
df = (spark.readStream
      .format("eventhubs")
      .options(**eh_config)
      .load())

# Process...

query = (df.writeStream
         .format("delta")
         .option("checkpointLocation", checkpoint_path)
         .trigger(processingTime="30 seconds")
         .start(output_path))
```

### Checkpoint Management
- Stored in ADLS Gen2 alongside data
- Per-consumer-group checkpoints
- Recovery: Delete checkpoint to reprocess from beginning (use with caution)

### Trigger Modes
- `processingTime("30 seconds")`: Continuous micro-batch (production streaming)
- `availableNow=True`: Process all available then stop (scheduled batch)
- `once=True`: Deprecated, use `availableNow`

## Schema Evolution

### Forward-Compatible Evolution
- New columns added with defaults (doesn't break existing readers)
- `mergeSchema=True` on writes to auto-evolve Delta schema
- Schema registry pattern not used (schema embedded in Delta metadata)

### Breaking Changes
- Column renames require migration notebook
- Type changes require careful null handling
- Gold tables: Add new columns, never remove (consumers may depend on them)

## Shadow Testing

### Pattern
- Run new logic in parallel with production (shadow mode)
- Compare outputs without affecting live data
- Validate before switching production to new logic

### Implementation
1. Duplicate pipeline with shadow suffix
2. Write to shadow table (e.g., `gold.fact_transactions_shadow`)
3. Run comparison queries to verify equivalence
4. Promote shadow to production once validated

## Module Pattern (BillingService)

Processing logic split into composable modules:
```
Main Notebook (orchestrator)
  └── Modules/
      ├── Transformation.py   # Column mapping, type casting
      ├── Deduplication.py    # Remove duplicates by key
      ├── Enrichment.py       # Join with dimensions
      └── Processor.py        # Merge to gold table
```

## Broadcast Joins

- Use `broadcast()` hint for small-side joins (< 100K rows)
- Avoids expensive shuffle operations
- Common for dimension joins in gold processing

## Lazy Evaluation

- Avoid `.collect()` and `.count()` in production code paths
- Use accumulator-based counting if metrics needed
- Prefer `.isEmpty()` over `.count() == 0`
