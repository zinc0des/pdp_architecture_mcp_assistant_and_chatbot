# KT Session Cheatsheet: MerchantDescriptor Normalization

> **Format:** 45-min recorded session · Live demo in Databricks + Azure Portal  
> **Handout:** Share `docs/KT-MerchantDescriptor-Normalization.md` with attendees BEFORE the session  
> **Recording tip:** Share screen with Databricks open; keep this cheatsheet on a second monitor

---

## Pre-Session Checklist

- [ ] Handout shared with attendees (at least 1 day prior)
- [ ] Databricks workspace open → navigate to `PaymentTransactions/Gold/`
- [ ] Second tab: `PaymentTransactions/Silver/Transactions/TransactionsTable.py`
- [ ] Third tab: `PaymentTransactions/Test/Integration/merchantdescriptor_completeness_accuracy_test.py`
- [ ] Fourth tab: `Gold/ShadowStreaming/Gold-DimMerchant-ShadowStreaming.py`
- [ ] Azure Portal open → DQ Framework / Grafana dashboard (optional)
- [ ] Recording started + confirm attendees can see your screen
- [ ] Introduce yourself and state the session will be recorded

---

## Session Flow (45 min)

### 🟢 Opening (3 min)

**SAY:**
> "This session covers how we solved the MerchantDescriptor cardinality problem — going from millions of raw merchant values down to about 50 normalized categories. I'll walk through the three-column design, show the actual code, and cover how we tested and rolled it out safely."

**MENTION:**
- Handout was shared — they can follow along and reference later
- Q&A at the end, but feel free to drop questions in chat

---

### 🔵 Part 1: The Problem (5 min)

**TALK THROUGH:**
- Raw `MerchantDescriptor` values: `MICROSOFT-G136136964`, `MSFT*XBOX GAME PASS`, etc.
- Millions of unique strings → `dim_merchant` table bloats
- Cube performance degrades, BI slicing is useless
- Show a concrete example: "If an analyst tries to slice by Microsoft, they get thousands of rows instead of one"

**OPTIONAL DEMO:** Query `dim_merchant` in Databricks to show cardinality:
```sql
SELECT COUNT(DISTINCT MerchantDescriptor) FROM gold.dim_merchant
-- vs
SELECT COUNT(DISTINCT MerchantDescriptor_vNext) FROM gold.transactions
```

---

### 🔵 Part 2: Three-Column Design (7 min)

**TALK THROUGH:**
- Three columns: `_Source` (raw), `MerchantDescriptor` (normalized), `_vNext` (enhanced)
- Why three? → `_Source` is audit trail, `_vNext` lets us iterate without breaking existing reports
- Normalization uses regex patterns: RLIKE/LIKE for Microsoft, MSFT, Xbox, 365, Battle.net variants
- Cross-repo: logic originates in PaymentsJournal, flows through BillingService

**SHOW IN DATABRICKS:**
1. Open `TransactionsTable.py` → show the `ALTER TABLE ADD COLUMNS` (line ~244)
2. Point out the `try/except` for idempotency — "already exists" is swallowed

**SAY:**
> "We add the columns via schema evolution, not table recreation. The try/except makes it safe to re-run."

---

### 🔵 Part 3: Data Flow — Silver to Gold (10 min)

**TALK THROUGH:**
- Flow: Silver Stage1 → Stage2 → Stage3 → Gold PaymentsJournal → Gold Billing → Gold DimMerchant → Gold FactTransactions → Cube

**SHOW IN DATABRICKS (Gold-DimMerchant.py):**
1. Navigate to line ~68 — the `lit(None).cast('string')` override
2. Explain: "During validation, we set MerchantDescriptor to null so the dimension collapses to one row per merchant key combo — this lets us ship without risk"
3. Show the MERGE pattern (lines ~84-105) — point out `<=>` null-safe equality
4. **Key callout:** "If you use `=` instead of `<=>`, null values won't match and you get duplicate dim rows"

**SHOW IN DATABRICKS (Gold-FactTransactions.py):**
1. Navigate to line ~382 — same `lit(None)` pattern
2. Show the `left_outer` join with dim_merchant
3. **Key callout:** "Both files must agree — if DimMerchant uses null but FactTransactions doesn't, the FK join breaks"

**SHOW IN DATABRICKS (Gold-DimMerchant-ShadowStreaming.py):**
1. Navigate to line ~94 — the `coalesce` line
2. Explain: "Shadow streaming ran in parallel with the production path. It uses `coalesce(vNext, MerchantDescriptor)` — if vNext is populated, use it; otherwise fall back"
3. **Key callout:** "This is how we validated the normalization before full activation — shadow writes to `DIM_MERCHANT_VNEXT` while production writes to `DIM_MERCHANT`"

---

### 🔵 Part 4: Rollout Strategy (5 min)

**TALK THROUGH the timeline:**

| Phase | What happened |
|-------|---------------|
| Jul–Dec 2025 | Built normalization logic, added three columns |
| Feb 2026 | Shipped with null override — production safe, shadow validating |
| Feb 2026 | Shadow streaming activated with `coalesce` |
| Apr 6, 2026 | PR to remove null override → full activation |

**SAY:**
> "The key insight is the null override. We shipped the schema change to production but kept MerchantDescriptor as null. This means dim_merchant had exactly one row per merchant key combo — zero risk. Meanwhile, shadow streaming was writing the real normalized values to a separate table. Once we validated shadow matched expectations, we removed the null override."

**EMPHASIZE:**
- This pattern (ship schema → null override → shadow validate → activate) is reusable for future column changes

---

### 🔵 Part 5: Testing Strategy (10 min)

**TALK THROUGH the test layers:**

```
Canary (alerts on-call)
Integration (live table reads)
Shadow Diff (vNext vs production)
DQ Monitoring (Grafana)
```

**SHOW IN DATABRICKS (merchantdescriptor_completeness_accuracy_test.py):**

1. **Completeness test** (line ~61): "We check that the columns actually exist in the table"
2. **Accuracy test** (line ~85): Walk through the three assertions:
   - `vNext_cardinality < source_cardinality` → "Normalization must reduce cardinality"
   - `ms365_collapsed_incorrectly == 0` → "MICROSOFT 365 must NOT collapse to just MICROSOFT"
   - `gamepass_collapsed_incorrectly == 0` → "XBOX GAME PASS must NOT collapse to just XBOX"
3. **Point out the decorator** (line ~50): `is_canary="True"` means this feeds on-call alerting

**SAY:**
> "The accuracy test is the most important one. It's not enough to check that cardinality went down — we also check that we didn't collapse things that should stay separate. Microsoft 365 and Xbox are different products."

**MENTION (don't need to show):**
- Shadow diff test in `DimTables-ShadowDiffTest.py` — compares vNext vs production tables
- Grafana DQ rule in `gold_merchantdescriptor.json` — monitors cardinality daily
- All tests run via `Pytest-Runner.py` on Databricks jobs

---

### 🟢 Wrap-up & Q&A (5 min)

**SUMMARIZE:**
> "To recap: we went from millions of raw merchant descriptors to ~50 normalized categories using a three-column design with regex patterns. We rolled it out safely using a null override + shadow streaming validation pattern. Tests cover completeness, accuracy, shadow diff, and continuous Grafana monitoring."

**POINT TO:**
- Handout for all code file locations
- Common pitfalls section in the handout (null-safe equality, cross-repo dependency)
- Cube Optimization session (next) — "MerchantDescriptor normalization is Wave 1 enabler"

**OPEN FOR Q&A**

---

## Talking Points If Asked

| Question | Answer |
|----------|--------|
| "Why not just regex-replace in the cube?" | Normalization belongs in the data layer — doing it in DAX would be slow and unmaintainable at 4B rows |
| "What if a new merchant pattern appears?" | Add a new RLIKE pattern upstream in NormalizationAndEnrichment, it flows through automatically |
| "Why three columns, not two?" | `_vNext` lets us iterate on rules without breaking reports that already use `MerchantDescriptor` |
| "What about historical data?" | Backfill needed — existing rows have null `_vNext` until reprocessed |
| "How long did shadow validation run?" | ~2 months (Feb–Apr 2026) before full activation |
