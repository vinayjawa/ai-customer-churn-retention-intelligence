# Dataset Profile — IBM Telco Customer Churn

**Inspection date:** 2026-10-14  
**Project root:** `E:\Projects\AI-Powered Customer Churn Prediction & Retention Intelligence`  
**Method:** Read-only inspection via Python (`csv` stdlib and `pandas.read_csv`). The source file was not modified, renamed, or copied for profiling.

---

## 1. Located data file

| Attribute | Measured value |
|-----------|----------------|
| **Filename** | `WA_Fn-UseC_-Telco-Customer-Churn.csv` |
| **Format** | CSV (comma-separated, UTF-8) |
| **Size** | 977,501 bytes (~954 KB) |
| **Location** | Project root (same folder as this `docs/` directory) |

**Note:** No Excel (`.xlsx` / `.xls`) files were found under the project root at inspection time. If an Excel export exists elsewhere, it was not present in this workspace; the active dataset for the project is the CSV above unless you add another file explicitly.

---

## 2. Shape and target

| Metric | Measured value |
|--------|----------------|
| **Row count (records)** | 7,043 |
| **Column count** | 21 |
| **Primary key candidate** | `customerID` — 7,043 distinct values, 0 duplicate IDs |
| **Target (churn) column** | `Churn` |
| **Churn labels** | `No` (5,174), `Yes` (1,869) |
| **Churn rate (`Yes`)** | 26.54% (1,869 / 7,043) |
| **Full duplicate rows** | 0 |

---

## 3. Column inventory

| # | Column | Inferred role | Pandas dtype (on read) |
|---|--------|---------------|-------------------------|
| 1 | customerID | Identifier | string |
| 2 | gender | Feature | string |
| 3 | SeniorCitizen | Feature (0/1) | int64 |
| 4 | Partner | Feature | string |
| 5 | Dependents | Feature | string |
| 6 | tenure | Feature (months) | int64 |
| 7 | PhoneService | Feature | string |
| 8 | MultipleLines | Feature | string |
| 9 | InternetService | Feature | string |
| 10 | OnlineSecurity | Feature | string |
| 11 | OnlineBackup | Feature | string |
| 12 | DeviceProtection | Feature | string |
| 13 | TechSupport | Feature | string |
| 14 | StreamingTV | Feature | string |
| 15 | StreamingMovies | Feature | string |
| 16 | Contract | Feature | string |
| 17 | PaperlessBilling | Feature | string |
| 18 | PaymentMethod | Feature | string |
| 19 | MonthlyCharges | Feature | float64 |
| 20 | TotalCharges | Feature (stored as text) | string |
| 21 | Churn | **Target** | string |

---

## 4. Data quality findings (measured)

### 4.1 Missing values (pandas `isna()`)

- **All 21 columns:** 0 null/missing values after CSV load.

### 4.2 Blank / invalid `TotalCharges`

- **11 rows** have `TotalCharges` equal to a blank string (`""`), not pandas null.
- After `pd.to_numeric(..., errors="coerce")`, those **11 values become null**.
- For all 11 rows: **`tenure` = 0** (new customers with no accumulated charges yet).
- This pattern matches the well-known quirk in the public Kaggle IBM Telco dataset.

### 4.3 Categorical domains (unique values)

| Column | Unique values (count) |
|--------|------------------------|
| gender | Female, Male (2) |
| Partner, Dependents, PhoneService, PaperlessBilling, most Yes/No services | No, Yes (2) |
| MultipleLines | No, No phone service, Yes (3) |
| InternetService | DSL, Fiber optic, No (3) |
| OnlineSecurity, OnlineBackup, DeviceProtection, TechSupport, StreamingTV, StreamingMovies | No, No internet service, Yes (3) |
| Contract | Month-to-month, One year, Two year (3) |
| PaymentMethod | Bank transfer (automatic), Credit card (automatic), Electronic check, Mailed check (4) |
| Churn | No, Yes (2) |
| SeniorCitizen | 0 (5,901), 1 (1,142) |

### 4.4 Numeric summaries (measured)

**tenure (months)**

| stat | value |
|------|-------|
| min | 0 |
| max | 72 |
| mean | 32.37 |
| median (50%) | 29 |

**MonthlyCharges**

| stat | value |
|------|-------|
| min | 18.25 |
| max | 118.75 |
| mean | 64.76 |
| median | 70.35 |

**TotalCharges** (after numeric coercion; n = 7,032 valid)

| stat | value |
|------|-------|
| min | 18.80 |
| max | 8,684.80 |
| mean | 2,283.30 |
| median | 1,397.48 |

---

## 5. Comparison to standard IBM Telco Customer Churn (Kaggle)

The public dataset on Kaggle ([IBM Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)) is commonly distributed as **`WA_Fn-UseC_-Telco-Customer-Churn.csv`** with **7,043 rows** and **21 columns**, including target **`Churn`** (`Yes` / `No`).

**Measured alignment with that reference:**

| Check | Result |
|-------|--------|
| Filename | Matches typical Kaggle CSV name |
| Row/column count | 7,043 × 21 — matches |
| Column names and order (header) | Matches standard listing |
| Churn class counts | Not byte-compared to Kaggle; counts are internally consistent |
| 11 blank `TotalCharges` at `tenure = 0` | Present — matches known reference behavior |
| Excel variant | **Not present** in project folder |

**Differences / caveats (not assumptions):**

- We did **not** diff this file against a separate official checksum; alignment is based on structure, size, and known reference patterns.
- **`TotalCharges`** is read as **string** in pandas because of blank values; SQL and ML pipelines should cast explicitly and impute or derive charges for tenure-0 rows (decision deferred to Phase 2+).

---

## 6. Implications for SQL Server and modeling (planning only)

| Topic | Recommendation |
|-------|----------------|
| Staging load | Load CSV as-is; cast `TotalCharges` to `DECIMAL` with NULL for blanks |
| Primary key | `customerID` (NVARCHAR) |
| Target | `Churn` → bit or char; map `Yes`/`No` to 1/0 for ML |
| Data-quality rules | Flag tenure=0 + null TotalCharges; no duplicate customerID |
| Leakage | Do not use post-churn-only fields; this dataset has no obvious temporal leakage columns beyond standard telco features |

---

## 7. Reproducibility

Inspection commands used Python **3.14.7** with **pandas 3.0.6** on the local machine. To re-run a minimal profile without changing the file:

```python
import pandas as pd
path = r"WA_Fn-UseC_-Telco-Customer-Churn.csv"  # project root
df = pd.read_csv(path)
print(df.shape, df["Churn"].value_counts())
print(df.isna().sum())
print((df["TotalCharges"].str.strip() == "").sum())
```

---

*End of dataset profile. Statistics in sections 2–4 are measured from the local file unless labeled as planning recommendation.*
