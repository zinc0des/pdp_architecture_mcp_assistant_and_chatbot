# Payment Analytics Cube — Optimization Proposal

**Date:** 2026-03-18 | **From:** Data Science Team | **Status:** Draft for Discussion

## 1. Context

Following conversations with Bhupinder, I believe there is a strong opportunity to optimize the Payment Analytics semantic model (cube). We recognize that PDP has cube-side usage telemetry that is likely more authoritative for identifying low-usage measures. This proposal complements that data with the Data Science team's perspective on which measures and dimensions we actually consume, which ones create confusion, and where consolidation would improve maintainability and clarity.

## 2. Current State

The cube currently contains approximately 270 measures across 22 dimension tables with ~130 dimension columns. Many of these measures are pre-segmented variants of a smaller set of core metrics, and several dimensions carry redundant or rarely used columns. This creates unnecessary maintenance burden, slows model refresh, and makes the cube harder for analysts to navigate.

## 3. Recommendations

### 3.1 Consolidate Dunning Commercial & Consumer Measures

The cube currently maintains separate measure families for dunning Commercial and dunning Consumer — for example `Pmt_Approval#%_Dun_Commercial` vs `Pmt_Approval#%_Dun_Consumer`. The calculation pattern is identical; the only difference is the ConsumerOrCommercial segment baked into the measure.

**Recommendation:** Consolidate into a single `_Dun` family (e.g. `Pmt_Approval#%_Dun`, `Pmt_Total#_Dun`, etc.) and let the existing ConsumerOrCommercial dimension column handle the segmentation at the report layer. This alone removes ~24 redundant measures.

| Current Measures (remove) | Proposed Replacement |
|---|---|
| `Pmt_Approval#%_Dun_Commercial`, `Pmt_Approval#%_Dun_Consumer` | `Pmt_Approval#%_Dun` |
| `Pmt_Approval$%_Dun_Commercial`, `Pmt_Approval$%_Dun_Consumer` | `Pmt_Approval$%_Dun` |
| `Pmt_Approval#_Dun_Commercial`, `Pmt_Approval#_Dun_Consumer` | `Pmt_Approval#_Dun` |
| `Pmt_Approval$_Dun_Commercial`, `Pmt_Approval$_Dun_Consumer` | `Pmt_Approval$_Dun` |
| `Pmt_Decline#_Dun_Commercial`, `Pmt_Decline#_Dun_Consumer` | `Pmt_Decline#_Dun` |
| `Pmt_Decline$_Dun_Commercial`, `Pmt_Decline$_Dun_Consumer` | `Pmt_Decline$_Dun` |
| `Pmt_Total#_Dun_Commercial`, `Pmt_Total#_Dun_Consumer` | `Pmt_Total#_Dun` |
| `Pmt_Total$_Dun_Commercial`, `Pmt_Total$_Dun_Consumer` | `Pmt_Total$_Dun` |
| + all `_FA` variants of the above | + `_Dun_FA` variants |
| + all Forecast `_Dun_Commercial` / `_Dun_Consumer` | (see Forecast section) |

### 3.2 Remove Pre-Segmented _CI and _MI Measures

The cube carries separate `_CI` and `_MI` variants for approval, decline, and total counts and rates. Since DimPayment already exposes `CustomerOrMerchantInitiated` as a dimension column, any report can filter or slice by CIT vs MIT without needing dedicated measures. These pre-segmented measures add ~30+ measures to the model.

**Recommendation:** Remove `_CI`, `_MI`, and `_CI_AA` measure families. Keep the base measures (e.g. `Pmt_Approval#%`, `Pmt_Approval$%`) and let the `CustomerOrMerchantInitiated` dimension handle segmentation.

### 3.3 Revamp Forecast Measures

The current forecast measures (`Pmt_Approval_Forecast#%`, `Pmt_Approval_Forecast$%`, and their `_MI`, `_Dun_Commercial`, `_Dun_Consumer` variants) are producing incorrect values. These need to be redesigned from scratch rather than patched.

**Recommendation:** Temporarily hide or remove all 8 forecast measures from the cube. The Data Science team will work with the cube team to define a correct forecasting methodology, after which new forecast measures can be reintroduced. This avoids downstream consumers relying on inaccurate forecasts.

### 3.4 Remove Time Intelligence Measures (YTD, MTD, DoD, MoM, YoY)

The cube contains a large family of time-intelligence measures — YTD, PYTD, MTD, PMTD, Day, PDay, `_Avg`, and the corresponding DoD / MoM / YoY percentage change and formatted variants. These account for roughly **80–90 measures** across Payment, Validate, Refund, and Chargeback domains.

**Recommendation:** Remove all time intelligence measures from the semantic model. Time intelligence calculations are straightforward in DAX at the report layer and do not need to be baked into the cube. Removing them dramatically simplifies the model and eliminates a major source of maintenance overhead whenever new base measures are added.

### 3.5 Remove Previous Year Comparison Measures

Approximately **15** `_PreviousYear` measures exist across approval, validate, refund, and chargeback families. Like time intelligence, these are easily computed at the report layer using `SAMEPERIODLASTYEAR` or `DATEADD`.

**Recommendation:** Remove all `_PreviousYear` measures.

### 3.6 Remove Provider / Method / Bank Share Breakdown Measures

The cube contains **~12** provider/method/bank share measures (e.g. `%Pmt_Approval$_By_ProviderName`, `%Pmt_Approval$_By_ProviderName_CI`, `_MI`, `_Consumer`, `_Commercial`, `_Credit`, `_Debit`, `_Prepaid`, `By_IssuingBank`, `By_PaymentMethod`). These are simple `DIVIDE(slice, total)` calculations that any Power BI report can compute by placing the dimension on rows.

**Recommendation:** Remove all share-of-provider / share-of-method measures. The base amount measures (`Pmt_Approval$`, etc.) combined with the existing dimension columns (`ProviderName`, `PaymentMethodType`, `IssuerName`) are sufficient.

### 3.7 Consider Removing Decline Code Breakdown Measures

The `_Total_By_ResponseCodeFromNetwork` and `%_By_DeclineCodes` measures are share-of-total calculations that can be done at the report layer. Consider removing or hiding these as well.

## 4. Dimension Cleanup Recommendations

### 4.1 Retire DimDunning — Keep Only DimDunningNew

The cube contains both DimDunning (9 columns) and DimDunningNew (11 columns). DimDunningNew is the authoritative dunning dimension with the ByCycle logic. The legacy DimDunning should be removed entirely to avoid confusion.

### 4.2 DimPayment — Evaluate Redundant Columns

DimPayment contains `IsRecurring`, but in practice the team always uses `CustomerOrMerchantInitiated` (CIT / MIT) instead. Consider hiding `IsRecurring` from the model or documenting it clearly so analysts know which to use. Additionally, `ResponseCodeFromProvider`, `ResponseResultFromProvider`, and `ResponseCodeFromNetwork` appear in both DimPayment and DimResponseCode — evaluate whether the DimPayment copies can be hidden.

### 4.3 DimGeo — Remove Duplicate Country/Currency Codes

DimGeo carries Country, Country_a2, Country_a3, Currency, and Currency_a3. We only need one country code variant and one currency code variant.

**Recommendation:** Keep Country (display name) + Country_a3 (for joins and maps). Remove Country_a2. Keep Currency + Currency_a3 (ISO standard). This removes 1–2 columns and reduces confusion about which code to use.

### 4.4 DimPurchase — MarketplaceCountry Duplication

DimPurchase has both `MarketplaceCountry` and `MarketplaceCountry_a2`. Same logic as DimGeo — keep one.

### 4.5 Hide _Source Columns

Several dimensions carry `_Source` variants (e.g. `ProviderName_Source`, `PaymentMethodFamily_Source`, `ResponseCodeFromProvider_Source`, `Storefront_Source`, `IssuerName_Source`, `PaymentNetworkName_Source`). These are internal lineage columns that are not used in analysis. Hide them from the report layer to reduce clutter.

## 5. Estimated Impact Summary

| Category | Current Count | Measures Removed | Remaining |
|---|:---:|:---:|:---:|
| Dunning Commercial/Consumer consolidation | ~24 | ~12 | ~12 (unified `_Dun`) |
| `_CI` / `_MI` pre-segmented removal | ~30 | ~30 | 0 (use dimension) |
| Forecast measures (hide/revamp) | ~8 | ~8 | 0 (pending redesign) |
| Time intelligence (YTD/MTD/DoD/MoM/YoY) | ~80-90 | ~80-90 | 0 (report layer) |
| Previous Year comparisons | ~15 | ~15 | 0 (report layer) |
| Provider/Method/Bank share breakdowns | ~12 | ~12 | 0 (report layer) |
| Decline code breakdowns | ~4 | ~4 | 0 (report layer) |
| | | | |
| **TOTAL MEASURES** | **~270** | **~160-170** | **~100-110** |

| Dimension Change | Action |
|---|---|
| DimDunning (legacy) | Remove — replaced by DimDunningNew |
| Country_a2 (DimGeo) | Remove — keep Country + Country_a3 |
| MarketplaceCountry_a2 (DimPurchase) | Remove — keep MarketplaceCountry |
| ~8 `_Source` columns across dims | Hide from report layer |
| IsRecurring (DimPayment) | Hide or document (use `CustomerOrMerchantInitiated`) |

## 6. Proposed Process

1. Cross-reference this proposal with cube-side usage telemetry (Bhupinder's team) to validate which measures are truly low-usage end-to-end.
2. Identify any downstream Power BI reports or dashboards that reference measures proposed for removal. Coordinate migration to dimension-based filtering.
3. Phase 1: Hide (do not delete) deprecated measures. Monitor for breakage over 1–2 refresh cycles.
4. Phase 2: Delete hidden measures after confirming no active dependencies.
5. Phase 3: Redesign forecast measures with correct methodology and reintroduce.

## 7. Open Questions

- Can we get a usage telemetry extract to cross-reference with this proposal?
- Are there any downstream consumers of the forecast measures that we should notify before hiding them?
- Is there a preferred deprecation timeline (e.g. FY26 Q4, next refresh cycle)?

---

*Prepared by: Data Science Team | For discussion with Bhupinder, Noam, and Cube Engineering*
