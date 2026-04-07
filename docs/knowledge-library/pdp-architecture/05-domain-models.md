# PDP Domain Models

## Overview

Each PDP domain has its own set of tables organized in the medallion pattern.
Gold tables follow star schema conventions where applicable.

## Payment Transactions (PMT)

### Gold Star Schema
- **gold.fact_transactions** — Core fact table with transaction lifecycle events
- **gold.dim_provider** — Payment provider dimension (Adyen, Worldpay, Chase, etc.)
- **gold.dim_paymentmethod** — Payment method dimension (credit card, debit, PayPal, etc.)
- **gold.dim_paymentmethodfamily** — Higher-level grouping (Card, Wallet, Bank Transfer)
- **gold.dim_currency** — Currency dimension
- **gold.dim_country** — Country/region dimension
- **gold.dim_merchant** — Merchant dimension
- **gold.dim_date** — Date dimension

### Key Columns (fact_transactions)
- TransactionId, PaymentInstrumentId
- AuthorizationAmount, CaptureAmount, SettlementAmount
- ApprovalStatus, DeclineReason, ResponseCode
- ProviderId, PaymentMethodId, CurrencyId, CountryId
- CreatedDate, ProcessedDate

## Cost of Payments (COP)

- **gold.cost_of_payments** — Aggregated fee data by provider, method, region
- **gold.billed_fees** — Individual fee records from provider statements
- Key metrics: Interchange fees, processing fees, network fees, total cost per transaction

## Fraud / PIMS

- **gold.fraud_metrics** — Aggregated fraud signals and scores
- Source: PIMS (Payment Instrument Management Service) events
- Key columns: RiskScore, FraudIndicator, ChargebackFlag

## Payments Journal

- **gold.payments_journal** — Complete journal of payment events
- 4-stage silver pipeline (Stage1 → Stage2 → Stage3 → Stage4)
- Uses liquid clustering on gold table
- CDF-enabled for downstream consumers

## BillingService

- **gold.billing** — Unified billing events (Modern, MCF, Legacy)
- **gold.payments_billing** — CDF-derived billing analytics table
- Billing types: ModernConsumer, ModernCommercial, MCF, Legacy, BingAds

## Network Tokenization (NT)

- **gold.network_tokenization** — Token lifecycle events
- Key columns: DPAN, TokenStatus, ProvisioningDate, TokenRequestorId

## Account Updater (AU)

- **gold.account_updater** — Card-on-file update events
- Key columns: OldPAN, NewPAN, UpdateReason, ExpirationDate

## BIN

- **gold.bin_reference** — Bank Identification Number reference data
- Used as enrichment dimension by PMT and other domains
- Key columns: BIN, IssuingBank, CardBrand, ProductType, CountryCode

## Reconciliation (Recon)

- **gold.reconciliation_variances** — Detected mismatches between systems
- Compares: PDP vs Provider settlements, PDP vs Commerce ledger
