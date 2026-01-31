# Nakamoto-30 Set Deep Analysis

## Overview

Analysis of the entities that together control at least 30% of Avalanche's total stake,
using extended validator data with GeoIP metadata.

**Data Period**: 2021-06-30 to 2026-01-31
**Quarterly Snapshots**: 19

## Current State (2026-01-31)

| Metric | Value |
|--------|-------|
| Entities in N30 Set | 11 |
| Validators Operated | 73 |
| Stake Controlled | 30.8% |
| Unique Countries | 8 |
| Unique ASNs | 15 |

## Geographic Diversity

| Metric | Current | Min | Max |
|--------|---------|-----|-----|
| Countries | 8 | 5 (2021-06-30) | 15 (2022-12-31) |
| ASNs | 15 | 4 (2023-12-31) | 15 (2025-09-30) |

## Current Top Entities

| Rank | Address | Stake % | Validators | Countries |
|------|---------|---------|------------|-----------|
| 1 | `P-avax19456a...e8fn` | 6.08% | 5 | DE |
| 2 | `P-avax19zfyg...dal0` | 5.84% | 24 | US, FI, DE, NL |
| 3 | `P-avax1p55uk...q0jz` | 4.00% | 4 | US |
| 4 | `P-avax13rs52...9frk` | 2.74% | 16 | IE |
| 5 | `P-avax1rr5nc...am7k` | 2.32% | 2 | US |
| 6 | `P-avax1q20ws...yeyt` | 1.90% | 2 | US |
| 7 | `P-avax1k4jtq...v3xe` | 1.82% | 2 | JP, US |
| 8 | `P-avax1hpx0u...pzrd` | 1.75% | 2 | JP |
| 9 | `P-avax1k8zd7...50n7` | 1.63% | 2 | TR |
| 10 | `P-avax1eeghh...syur` | 1.43% | 3 | DE, US |
| 11 | `P-avax10cdg4...w3rp` | 1.31% | 11 | US, CA |

## Country Distribution (Current)

| Country | Validators |
|---------|------------|
| NL | 19 |
| IE | 16 |
| US | 14 |
| CA | 10 |
| DE | 8 |
| JP | 3 |
| TR | 2 |
| FI | 1 |

## Hosting Provider Distribution (Current)

| Provider (ASN) | Validators |
|----------------|------------|
| moula world llc | 19 |
| Amazon Data Services Ireland Limited | 14 |
| OVH Hosting, Inc. | 10 |
| A100 Row GmbH | 6 |
| Google LLC | 5 |
| Netcup GmbH | 5 |
| Amazon.com, Inc. | 3 |
| Allnodes Inc. | 3 |
| AT ANXHOLDING 1 00 | 2 |
| Amazon Data Services Japan | 1 |

## Entity Persistence Analysis

How long do entities stay in the Nakamoto-30 set?

**Total unique entities ever in N30**: 160

### Persistent Entities (>50% of time in N30)
- `P-avax1hpx0u...pzrd`: 17/19 quarters (89%)

### Occasional Entities (25-50% of time in N30)
- `P-avax13pnjc...khp0`: 8/19 quarters (42%)
- `P-avax1m9swq...83x3`: 7/19 quarters (37%)
- `P-avax1k4jtq...v3xe`: 7/19 quarters (37%)
- `P-avax1k8zd7...50n7`: 7/19 quarters (37%)
- `P-avax13rs52...9frk`: 5/19 quarters (26%)
- `P-avax1eeghh...syur`: 5/19 quarters (26%)

### Transient Entities (<25% of time in N30)

153 entities appeared briefly in the N30 set.

## Plots

- [Geographic Diversity](nakamoto_geography.png)
- [Country Distribution](nakamoto_countries.png)
- [ASN Concentration](nakamoto_asn_concentration.png)

## Key Findings

1. **Geographic Concentration**: The N30 set spans 8 countries
2. **Infrastructure Risk**: 15 unique hosting providers
3. **Entity Churn**: 160 unique entities have been in N30 over time
4. **Persistence**: 1 entities consistently control significant stake
