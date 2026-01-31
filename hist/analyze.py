#!/usr/bin/env python
###############################################################################
# Historical GINI & Nakamoto Coefficient Analysis for Avalanche Validators
# Analyzes validators grouped by reward address (ownership entities)
###############################################################################

import json
import numpy as np
import matplotlib.pyplot as pp
import os
import re
import csv
from datetime import date, datetime
from typing import List, Dict, Tuple, Any

###############################################################################

JSON_DIR = '../json'
HIST_DIR = '.'

def get_available_dates() -> List[str]:
    """Get all available date directories"""
    dates = []
    for d in os.listdir(JSON_DIR):
        if re.match(r'^\d{4}-\d{2}-\d{2}$', d):
            dates.append(d)
    return sorted(dates)

def get_quarterly_dates(dates: List[str]) -> List[str]:
    """Select quarterly dates (closest to quarter end)"""
    quarterly = []
    quarter_ends = ['03-31', '06-30', '09-30', '12-31']

    # Group dates by year-quarter
    quarters = {}
    for d in dates:
        dt = datetime.strptime(d, '%Y-%m-%d')
        year = dt.year
        quarter = (dt.month - 1) // 3 + 1
        key = (year, quarter)
        if key not in quarters:
            quarters[key] = []
        quarters[key].append(d)

    # For each quarter, pick the last available date
    for key in sorted(quarters.keys()):
        quarterly.append(quarters[key][-1])

    return quarterly

def load_validators(data_path: str) -> List[Dict]:
    """Load validators from JSON file"""
    json_path = os.path.join(data_path, 'validators.json')
    if not os.path.exists(json_path):
        return []
    with open(json_path) as f:
        return json.load(f)

def by_address(validators: List[Dict]) -> List[Dict]:
    """Group validators by reward address (entity)"""
    groups = {}
    for v in validators:
        key = frozenset(v['rewardAddresses'])
        if key not in groups:
            groups[key] = {
                'id': set(),
                'rewardAddresses': set(),
                'weight': 0,
                'delegatorWeight': 0,
                'totalWeight': 0
            }
        g = groups[key]
        vid = v['id']
        g['id'].update(vid if isinstance(vid, list) else [vid])
        g['rewardAddresses'].update(v['rewardAddresses'])
        g['weight'] += v['weight']
        # Handle both old (delegatedWeight) and new (delegatorWeight) field names
        g['delegatorWeight'] += v.get('delegatorWeight', v.get('delegatedWeight', 0))
        g['totalWeight'] += v['totalWeight']
    return list(groups.values())

def gini(a: np.ndarray) -> float:
    """Compute GINI coefficient of inequality"""
    if len(a) == 0:
        return 0.0
    a = np.array(a, dtype=np.float64)
    mad = np.abs(np.subtract.outer(a, a)).mean()
    return mad / np.mean(a) * 0.5

def nakamoto(weights: np.ndarray, threshold: float = 0.30) -> int:
    """
    Compute Nakamoto coefficient: minimum entities controlling >= threshold of stake
    Entities are sorted by stake descending, then count how many needed for threshold
    """
    if len(weights) == 0:
        return 0
    weights = np.array(weights, dtype=np.float64)
    total = np.sum(weights)
    sorted_weights = np.sort(weights)[::-1]  # Descending
    cumsum = np.cumsum(sorted_weights)
    target = total * threshold
    # Find first index where cumsum >= target
    idx = np.searchsorted(cumsum, target, side='left')
    return int(idx + 1)

def analyze_date(date_str: str) -> Dict:
    """Analyze a single date's data"""
    data_path = os.path.join(JSON_DIR, date_str)
    validators = load_validators(data_path)

    if not validators:
        return None

    # Group by reward address (entity)
    entities = by_address(validators)

    # Extract weights
    total_weights = np.array([e['totalWeight'] for e in entities], dtype=np.float64)
    own_weights = np.array([e['weight'] for e in entities], dtype=np.float64)

    total_stake = np.sum(total_weights)

    return {
        'date': date_str,
        'num_validators': len(validators),
        'num_entities': len(entities),
        'total_stake_avax': total_stake / 1e9,  # Convert to AVAX (nanoAVAX -> AVAX)
        'gini_total': gini(total_weights) * 100,  # As percentage
        'gini_own': gini(own_weights) * 100,
        'nakamoto_30': nakamoto(total_weights, 0.30),
        'nakamoto_33': nakamoto(total_weights, 0.33),
        'nakamoto_50': nakamoto(total_weights, 0.50),
    }

def analyze_all_quarterly() -> List[Dict]:
    """Analyze all quarterly data points"""
    dates = get_available_dates()
    quarterly_dates = get_quarterly_dates(dates)

    results = []
    for d in quarterly_dates:
        print(f"Analyzing {d}...")
        result = analyze_date(d)
        if result:
            results.append(result)

    return results

def save_csv(results: List[Dict], filename: str):
    """Save results to CSV"""
    if not results:
        return

    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

def print_table(results: List[Dict]):
    """Print results as formatted table"""
    print()
    print("=" * 120)
    print("AVALANCHE VALIDATOR STAKE DISTRIBUTION - QUARTERLY ANALYSIS (Grouped by Reward Address)")
    print("=" * 120)
    print()
    print(f"{'Quarter':<12} {'Date':<12} {'Validators':>10} {'Entities':>10} {'Stake (M)':>12} {'GINI %':>10} {'Nakamoto':>10}")
    print(f"{'':12} {'':12} {'':>10} {'':>10} {'':>12} {'(total)':>10} {'(30%)':>10}")
    print("-" * 120)

    for r in results:
        dt = datetime.strptime(r['date'], '%Y-%m-%d')
        quarter = f"{dt.year}Q{(dt.month-1)//3+1}"
        stake_m = r['total_stake_avax'] / 1e6  # to Millions
        print(f"{quarter:<12} {r['date']:<12} {r['num_validators']:>10} {r['num_entities']:>10} "
              f"{stake_m:>12.1f} {r['gini_total']:>10.1f} {r['nakamoto_30']:>10}")

    print("-" * 120)
    print()

def plot_gini_history(results: List[Dict]):
    """Plot GINI coefficient over time"""
    dates = [datetime.strptime(r['date'], '%Y-%m-%d') for r in results]
    gini_total = [r['gini_total'] for r in results]
    gini_own = [r['gini_own'] for r in results]

    pp.figure(figsize=(14, 6))
    pp.plot(dates, gini_total, 'o-', color='darkred', linewidth=2, markersize=6,
            label='GINI (incl. delegations)')
    pp.plot(dates, gini_own, 'o-', color='darkblue', linewidth=2, markersize=6,
            label='GINI (excl. delegations)')

    pp.xlabel('Date')
    pp.ylabel('GINI Coefficient (%)')
    pp.title('Avalanche Validator Stake GINI Coefficient Over Time\n(Grouped by Reward Address)', weight='bold')
    pp.legend(loc='best')
    pp.grid(True, alpha=0.3)
    pp.ylim(0, 100)

    # Reference lines
    pp.axhline(y=33.3, color='gray', linestyle=':', alpha=0.5, label='Uniform random (33.3%)')
    pp.axhline(y=66.6, color='gray', linestyle='--', alpha=0.5, label='Log-logistic (66.6%)')

    pp.tight_layout()
    pp.savefig(os.path.join(HIST_DIR, 'gini_history.svg'))
    pp.savefig(os.path.join(HIST_DIR, 'gini_history.png'), dpi=150)
    print("Saved gini_history.svg and gini_history.png")

def plot_nakamoto_history(results: List[Dict]):
    """Plot Nakamoto coefficient over time"""
    dates = [datetime.strptime(r['date'], '%Y-%m-%d') for r in results]
    nakamoto_30 = [r['nakamoto_30'] for r in results]
    nakamoto_33 = [r['nakamoto_33'] for r in results]
    nakamoto_50 = [r['nakamoto_50'] for r in results]

    pp.figure(figsize=(14, 6))
    pp.plot(dates, nakamoto_30, 'o-', color='darkgreen', linewidth=2, markersize=6,
            label='Nakamoto @ 30%')
    pp.plot(dates, nakamoto_33, 's-', color='darkorange', linewidth=2, markersize=6,
            label='Nakamoto @ 33%')
    pp.plot(dates, nakamoto_50, '^-', color='darkviolet', linewidth=2, markersize=6,
            label='Nakamoto @ 50%')

    pp.xlabel('Date')
    pp.ylabel('Nakamoto Coefficient (# of entities)')
    pp.title('Avalanche Nakamoto Coefficient Over Time\n(Min. entities to control X% of stake, grouped by reward address)', weight='bold')
    pp.legend(loc='best')
    pp.grid(True, alpha=0.3)

    pp.tight_layout()
    pp.savefig(os.path.join(HIST_DIR, 'nakamoto_history.svg'))
    pp.savefig(os.path.join(HIST_DIR, 'nakamoto_history.png'), dpi=150)
    print("Saved nakamoto_history.svg and nakamoto_history.png")

def plot_combined(results: List[Dict]):
    """Plot combined GINI and Nakamoto with dual axes"""
    dates = [datetime.strptime(r['date'], '%Y-%m-%d') for r in results]
    gini_total = [r['gini_total'] for r in results]
    nakamoto_30 = [r['nakamoto_30'] for r in results]

    fig, ax1 = pp.subplots(figsize=(14, 6))

    # GINI on left axis
    color1 = 'darkred'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('GINI Coefficient (%)', color=color1)
    line1 = ax1.plot(dates, gini_total, 'o-', color=color1, linewidth=2, markersize=6,
                     label='GINI (incl. delegations)')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_ylim(0, 100)
    ax1.grid(True, alpha=0.3)

    # Nakamoto on right axis
    ax2 = ax1.twinx()
    color2 = 'darkgreen'
    ax2.set_ylabel('Nakamoto Coefficient @ 30%', color=color2)
    line2 = ax2.plot(dates, nakamoto_30, 's-', color=color2, linewidth=2, markersize=6,
                     label='Nakamoto @ 30%')
    ax2.tick_params(axis='y', labelcolor=color2)

    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right')

    pp.title('Avalanche Decentralization Metrics Over Time\n(Grouped by Reward Address)', weight='bold')
    fig.tight_layout()
    pp.savefig(os.path.join(HIST_DIR, 'combined_history.svg'))
    pp.savefig(os.path.join(HIST_DIR, 'combined_history.png'), dpi=150)
    print("Saved combined_history.svg and combined_history.png")

def plot_entities_vs_validators(results: List[Dict]):
    """Plot number of entities vs validators over time"""
    dates = [datetime.strptime(r['date'], '%Y-%m-%d') for r in results]
    validators = [r['num_validators'] for r in results]
    entities = [r['num_entities'] for r in results]

    pp.figure(figsize=(14, 6))
    pp.plot(dates, validators, 'o-', color='steelblue', linewidth=2, markersize=6,
            label='Validators (nodes)')
    pp.plot(dates, entities, 's-', color='coral', linewidth=2, markersize=6,
            label='Entities (by reward address)')

    pp.xlabel('Date')
    pp.ylabel('Count')
    pp.title('Avalanche Validators vs Entities Over Time', weight='bold')
    pp.legend(loc='best')
    pp.grid(True, alpha=0.3)

    pp.tight_layout()
    pp.savefig(os.path.join(HIST_DIR, 'entities_history.svg'))
    pp.savefig(os.path.join(HIST_DIR, 'entities_history.png'), dpi=150)
    print("Saved entities_history.svg and entities_history.png")

def write_summary(results: List[Dict]):
    """Write summary markdown file"""
    if not results:
        return

    latest = results[-1]
    earliest = results[0]

    summary = f"""# Avalanche Validator Stake Distribution Analysis

## Summary

Analysis of GINI and Nakamoto coefficients for Avalanche validators,
**grouped by reward address** (i.e., ownership entities).

- **Data Period**: {earliest['date']} to {latest['date']}
- **Data Points**: {len(results)} quarterly snapshots

## Latest Metrics ({latest['date']})

| Metric | Value |
|--------|-------|
| Total Validators | {latest['num_validators']:,} |
| Unique Entities | {latest['num_entities']:,} |
| Total Stake | {latest['total_stake_avax']/1e6:.1f}M AVAX |
| GINI (incl. delegations) | {latest['gini_total']:.1f}% |
| GINI (excl. delegations) | {latest['gini_own']:.1f}% |
| Nakamoto @ 30% | {latest['nakamoto_30']} entities |
| Nakamoto @ 33% | {latest['nakamoto_33']} entities |
| Nakamoto @ 50% | {latest['nakamoto_50']} entities |

## Key Definitions

- **GINI Coefficient**: Measures stake inequality (0% = perfect equality, 100% = one entity holds all)
- **Nakamoto Coefficient @ X%**: Minimum number of entities that together control at least X% of total stake
- **Entity**: A group of validators sharing the same reward address(es)

## Quarterly Data

| Quarter | Date | Validators | Entities | Stake (M AVAX) | GINI (%) | Nakamoto (30%) |
|---------|------|------------|----------|----------------|----------|----------------|
"""

    for r in results:
        dt = datetime.strptime(r['date'], '%Y-%m-%d')
        quarter = f"{dt.year}Q{(dt.month-1)//3+1}"
        stake_m = r['total_stake_avax'] / 1e6
        summary += f"| {quarter} | {r['date']} | {r['num_validators']:,} | {r['num_entities']:,} | {stake_m:.1f} | {r['gini_total']:.1f} | {r['nakamoto_30']} |\n"

    summary += """
## Plots

- [GINI History](gini_history.svg)
- [Nakamoto History](nakamoto_history.svg)
- [Combined Metrics](combined_history.svg)
- [Validators vs Entities](entities_history.svg)

## Interpretation

- **Higher GINI** = more concentrated stake distribution (less decentralized)
- **Lower Nakamoto** = fewer entities needed to control significant stake (less decentralized)
- Ideal: Low GINI (< 50%) and High Nakamoto (> 20 for 33%)
"""

    with open(os.path.join(HIST_DIR, 'SUMMARY.md'), 'w') as f:
        f.write(summary)
    print("Saved SUMMARY.md")

###############################################################################

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("Analyzing quarterly data...")
    results = analyze_all_quarterly()

    print_table(results)

    print("\nGenerating outputs...")
    save_csv(results, os.path.join(HIST_DIR, 'quarterly_data.csv'))
    print("Saved quarterly_data.csv")

    plot_gini_history(results)
    plot_nakamoto_history(results)
    plot_combined(results)
    plot_entities_vs_validators(results)
    write_summary(results)

    print("\nDone!")
