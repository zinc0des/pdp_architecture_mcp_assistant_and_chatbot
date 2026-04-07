# KT Session Cheatsheet: Cube Optimization & Benchmark Infrastructure

> **Format:** 45-min recorded session · Live demo in Databricks + Azure Portal  
> **Handout:** Share `docs/KT-Cube-Optimization-Benchmark-Infrastructure.md` with attendees BEFORE the session  
> **Recording tip:** Share screen with the optimization plan doc open; keep this cheatsheet on a second monitor

---

## Pre-Session Checklist

- [ ] Handout shared with attendees (at least 1 day prior)
- [ ] `docs/PaymentTransactions_Cube_Optimization_Plan.md` open in browser/editor
- [ ] Databricks workspace open → `Gold/Gold-FactTransactions.py`
- [ ] Azure Portal → Synapse Studio → `CubeRefresh_WithRetry` pipeline
- [ ] Azure Portal → App Insights / Workbook for benchmark dashboard (if available)
- [ ] Grafana → DQ dashboard for gold layer (optional)
- [ ] Recording started + confirm attendees can see your screen
- [ ] Introduce yourself and state the session will be recorded

---

## Session Flow (45 min)

### 🟢 Opening (3 min)

**SAY:**
> "This session covers how we're optimizing the PaymentTransactions cube from 4.18 billion rows down to 628 million — an 85% reduction. I'll walk through the three-wave plan, the automated retry pipeline we built for cube refresh, the benchmark infrastructure, and how we test all of it."

**MENTION:**
- Handout was shared — they can follow along
- This builds on the MerchantDescriptor normalization session (Wave 1 enabler)
- Q&A at the end

---

### 🔵 Part 1: The Problem (5 min)

**TALK THROUGH:**
- 4.18B rows in `gold.fact_transactions` with 21 FK joins
- 432 DAX measures in the AAS cube
- 15–65 second render times per Power BI visual
- S4 AAS SKU at $8.06/hr — most expensive tier
- Cube refresh failures → manual on-call re-trigger

**SHOW (Optimization Plan doc):**
- Open `PaymentTransactions_Cube_Optimization_Plan.md`
- Show the Executive Summary table (lines ~70-77):

| Metric | Current | After Wave 1 | After Wave 2 | After Wave 3 |
|--------|:-------:|:------------:|:------------:|:------------:|
| Measures | 432 | 146 | 146 | 146 |
| Fact Rows | 4.18B | 4.18B | 628M | 628M |
| AAS SKU | S4 | S4→S2 | S2→S1 | S1 |

**SAY:**
> "The key insight is that this isn't just one optimization — it's three independent waves that compound. Waves 1 and 2 can run in parallel."

---

### 🔵 Part 2: Wave 1 — Semantic Layer Cleanup (8 min)

**TALK THROUGH:**
- 596 AAS tokens classified from 90-day telemetry
- 432 actual measures → 146 survivors (66% reduction)
- Three risk tiers: HIDE_NOW (204), HIDE_AFTER_NOTICE (43), MIGRATE_FIRST (39)

**SHOW (Optimization Plan doc):**
- Scroll to Wave 1 section — show the Mermaid architecture diagram
- Show the risk tier breakdown

**SAY:**
> "We used AzureDiagnostics QueryEnd events over 90 days to classify every measure. 204 measures had literally zero consumers — those are HIDE_NOW. 43 had some usage but are duplicates — we notify consumers then hide. 39 need replacement measures built first."

**KEY CALLOUTS:**
- "Measures are **hidden**, not deleted — this is reversible"
- "Categories removed: Time Intelligence variants, MI/CI duplicates, dunning splits, forecast breakdowns"
- "Wave 1 is owned by Data Science, not PDP Engineering"

---

### 🔵 Part 3: Wave 2 — Star Schema Reduction (10 min)

**TALK THROUGH the three phases with the progression:**
```
4.18B → 3.02B → 1.25B → 628M  (85% total reduction)
```

**Phase 2.1 (3 min):**
- Denormalize Geo only — dim_geo (2,472 rows) has validated composite key `(Country, Currency)`
- Drop GeoId FK, inline 3 columns (Country, Region, Currency)
- dim_product (179 rows) and dim_purchase (4,856 rows) retain surrogate FK joins — no valid natural key exists
- "dim_geo is zero risk — 2,472 rows, composite key validated unique"

**Phase 2.2 (3 min):**
- BinId → BinCardType: 620K distinct values → 4–5 canonical values (requires case normalization first)
- "This is the single biggest win — 70% cumulative reduction"
- "We replace a high-cardinality FK with a canonicalized string column: Credit, Debit, Prepaid, Unknown"

**Phase 2.3 (4 min):**
- Drop 8 FKs where 0 of 230 DAX measures reference the dimension
- "We confirmed this via Model.bim static scan AND 90-day telemetry — zero queries"

**SHOW (Optimization Plan doc):**
- Show Phase 2.3 table — all 8 FKs with 0 measures
- **Key callout:** "MerchantId has cardinality 1 and 0 measures — that's the MerchantDescriptor normalization driving dim_merchant to collapse"

---

### 🔵 Part 4: Wave 3 — Cascade Optimization (3 min)

**TALK THROUGH:**
- Wave 1 measure removals cascade back to architecture
- If ALL measures for a dimension are hidden → FK becomes droppable
- One target: dim_chargeback (8 rows — hybrid approach recommended)

**SAY:**
> "Wave 3 is a feedback loop — it's gated on Wave 1 results. We run validation queries to check: are ALL dependent measures hidden? If yes, we can safely drop the FK."

---

### 🔵 Part 5: CubeRefresh Retry Pipeline (5 min)

**SHOW IN AZURE PORTAL (Synapse Studio):**
1. Navigate to `CubeRefresh_WithRetry` pipeline
2. Show the ForEach loop structure
3. Walk through the flow:
   - Loop up to 3 times
   - Check `CubeRefreshSuccess` variable
   - Execute `CubeRefreshViaFunctionApp`
   - On success → set flag → loop exits
   - On failure → wait 5 min → retry
   - After 3 failures → pipeline fails → on-call paged

**SAY:**
> "Before this pipeline, every cube refresh failure meant a manual re-trigger by the on-call person — often at 3 AM. Now, transient failures auto-recover. On-call only gets paged after all 3 attempts fail."

**KEY CALLOUT:**
- `isSequential: true` — retries happen one at a time
- Parameters are configurable: `MaxRetries`, `RetryIntervalSeconds`

---

### 🔵 Part 6: Testing Strategy (8 min)

**TALK THROUGH the test layers:**

```
Canary → feeds on-call alerts (SEV2.5+)
Integration → live table reads + DQ checks
Diff/Shadow → compare before/after or vNext vs prod
Unit → SparkTestBase with in-memory DataFrames
DQ Monitoring → Grafana rules (JSON config)
Benchmark → Load tests with App Insights telemetry
```

**SHOW IN DATABRICKS (briefly — don't deep-dive each file):**

1. **Test organization** — show the `Test/` directory structure:
   ```
   Test/Unit/ | Functional/ | Integration/ | Diff/ | Canary/
   ```

2. **Test decorator** — show any test file with `@pytest.mark.testclassification`:
   - Point out `is_canary`, `severity`, `alert_name`
   - "Every test self-describes its severity and alert routing"

3. **Gold consistency test** — mention `gold.transactions_Consistency_test.py`:
   - "Compares `fact_transactions` vs `gold.transactions` on AmountUSD and TransactionCount"
   - "This catches divergence after star schema changes"

4. **DQ monitoring** — mention Grafana rules:
   - "JSON rules in `DQFramework/RuleConfig/` define freshness, null rate, and cardinality checks"
   - "These run daily and feed Grafana dashboards"

5. **Benchmark tests** — mention the load test framework:
   - "DAX queries executed against AAS, telemetry sent to App Insights"
   - "Azure Workbook dashboard shows p50/p90/p95/p99 per visual"
   - "Always tag runs with labels: `baseline`, optimization name"

**SAY:**
> "The testing strategy has three layers: automated tests catch regressions in CI, DQ rules catch production anomalies, and benchmark tests measure the actual performance impact."

---

### 🟢 Wrap-up & Q&A (3 min)

**SUMMARIZE:**
> "To recap: we're reducing the cube from 4.18B to 628M rows through three waves — semantic cleanup, star schema denormalization, and cascading FK drops. The retry pipeline handles transient refresh failures. And we have a comprehensive test pyramid from unit tests through canary alerts plus continuous DQ monitoring."

**POINT TO:**
- Handout for all file locations and detailed tables
- Master plan doc for the full wave breakdown
- Validation queries in `pbi_dax_optimization_validation.kql`

**OPEN FOR Q&A**

---

## Talking Points If Asked

| Question | Answer |
|----------|--------|
| "Why not just scale up AAS?" | S4 is already $8.06/hr. Reducing data is cheaper and faster than throwing hardware at it |
| "What if a hidden measure is needed later?" | Measures are hidden, not deleted. Unhide in Model.bim and redeploy — takes minutes |
| "How do you validate Wave 2 doesn't break DAX?" | Model.bim static scan confirms 0 measures reference dropped FKs. Plus 90-day telemetry shows 0 queries |
| "Why denormalize instead of just dropping dims?" | Denormalization preserves the BI slicing capability. For dim_geo, we use a hybrid approach — inline Country/Region/Currency on the fact table and reconnect via composite natural key `(Country, Currency)`. dim_product and dim_purchase keep their surrogate FK joins because no valid natural key exists |
| "What about backfill for denormalized columns?" | One-time backfill job populates the inline columns from existing dimension tables |
| "How long does the fact table rebuild take?" | Depends on cluster size. Plan for a few hours in prod with proper partitioning |
| "What's the SKU cost difference?" | S4: $8.06/hr → S1: $2.02/hr = 50-75% savings = potentially $50K+/year |
| "Can Wave 3 run before Wave 2?" | No — Wave 3 depends on Wave 1 measure dispositions. Wave 2 is independent of both |
