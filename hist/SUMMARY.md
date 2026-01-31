# Avalanche Validator Stake Distribution Analysis

## Summary

Analysis of GINI and Nakamoto coefficients for Avalanche validators,
**grouped by reward address** (i.e., ownership entities).

- **Data Period**: 2021-06-30 to 2026-01-31
- **Data Points**: 20 quarterly snapshots

## Latest Metrics (2026-01-31)

| Metric | Value |
|--------|-------|
| Total Validators | 753 |
| Unique Entities | 563 |
| Total Stake | 232.3M AVAX |
| GINI (incl. delegations) | 80.7% |
| GINI (excl. delegations) | 82.5% |
| Nakamoto @ 30% | 11 entities |
| Nakamoto @ 33% | 13 entities |
| Nakamoto @ 50% | 30 entities |

## Key Definitions

- **GINI Coefficient**: Measures stake inequality (0% = perfect equality, 100% = one entity holds all)
- **Nakamoto Coefficient @ X%**: Minimum number of entities that together control at least X% of total stake
- **Entity**: A group of validators sharing the same reward address(es)

## Quarterly Data

| Quarter | Date | Validators | Entities | Stake (M AVAX) | GINI (%) | Nakamoto (30%) |
|---------|------|------------|----------|----------------|----------|----------------|
| 2021Q2 | 2021-06-30 | 970 | 907 | 205.9 | 89.5 | 8 |
| 2021Q3 | 2021-09-30 | 1,032 | 1,001 | 248.3 | 88.9 | 10 |
| 2021Q4 | 2021-12-31 | 1,173 | 1,123 | 233.7 | 90.2 | 10 |
| 2022Q1 | 2022-03-31 | 1,383 | 1,187 | 218.5 | 89.6 | 15 |
| 2022Q2 | 2022-06-30 | 1,315 | 1,116 | 245.5 | 88.1 | 19 |
| 2022Q3 | 2022-09-30 | 1,236 | 1,078 | 262.7 | 88.4 | 15 |
| 2022Q4 | 2022-12-31 | 1,197 | 944 | 263.2 | 91.5 | 11 |
| 2023Q1 | 2023-03-31 | 1,267 | 947 | 264.2 | 91.2 | 11 |
| 2023Q2 | 2023-06-30 | 1,253 | 1,079 | 268.2 | 87.4 | 18 |
| 2023Q3 | 2023-09-30 | 1,294 | 1,018 | 236.6 | 86.9 | 17 |
| 2023Q4 | 2023-12-31 | 1,677 | 1,049 | 262.8 | 86.8 | 23 |
| 2024Q1 | 2024-03-31 | 1,735 | 988 | 243.0 | 86.2 | 20 |
| 2024Q2 | 2024-06-30 | 1,572 | 998 | 255.8 | 85.2 | 21 |
| 2024Q3 | 2024-09-30 | 1,451 | 959 | 241.3 | 85.2 | 22 |
| 2024Q4 | 2024-12-31 | 1,472 | 885 | 209.6 | 85.1 | 19 |
| 2025Q1 | 2025-03-31 | 1,421 | 816 | 218.1 | 84.1 | 17 |
| 2025Q2 | 2025-06-30 | 1,434 | 753 | 221.7 | 82.9 | 17 |
| 2025Q3 | 2025-09-30 | 914 | 593 | 191.0 | 81.2 | 14 |
| 2025Q4 | 2025-12-09 | 829 | 597 | 209.7 | 79.4 | 15 |
| 2026Q1 | 2026-01-31 | 753 | 563 | 232.3 | 80.7 | 11 |

## Plots

- [GINI History](gini_history.svg)
- [Nakamoto History](nakamoto_history.svg)
- [Combined Metrics](combined_history.svg)
- [Validators vs Entities](entities_history.svg)

## Interpretation

- **Higher GINI** = more concentrated stake distribution (less decentralized)
- **Lower Nakamoto** = fewer entities needed to control significant stake (less decentralized)
- Ideal: Low GINI (< 50%) and High Nakamoto (> 20 for 33%)
