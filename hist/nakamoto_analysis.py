#!/usr/bin/env python
###############################################################################
# Nakamoto-30 Set Analysis - Deep dive into entities controlling 30% of stake
# Uses validators-ext.json for GeoIP metadata
###############################################################################

import json
import numpy as np
import matplotlib.pyplot as pp
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Dict, Tuple, Any, Set

###############################################################################

JSON_DIR = '../json'
HIST_DIR = '.'

def get_quarterly_dates() -> List[str]:
    """Get quarterly dates that have extended validator data"""
    dates = []
    for d in sorted(os.listdir(JSON_DIR)):
        if re.match(r'^\d{4}-\d{2}-\d{2}$', d):
            ext_path = os.path.join(JSON_DIR, d, 'validators-ext.json')
            if os.path.exists(ext_path):
                dates.append(d)

    # Select quarterly (last date of each quarter)
    quarters = {}
    for d in dates:
        dt = datetime.strptime(d, '%Y-%m-%d')
        key = (dt.year, (dt.month - 1) // 3 + 1)
        if key not in quarters:
            quarters[key] = []
        quarters[key].append(d)

    return [quarters[k][-1] for k in sorted(quarters.keys())]

def load_validators_ext(date_str: str) -> List[Dict]:
    """Load extended validators with GeoIP data"""
    path = os.path.join(JSON_DIR, date_str, 'validators-ext.json')
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)

def by_address_ext(validators: List[Dict]) -> List[Dict]:
    """Group validators by reward address, preserving GeoIP metadata"""
    groups = {}
    for v in validators:
        key = frozenset(v.get('rewardAddresses', []))
        if not key:
            continue
        if key not in groups:
            groups[key] = {
                'id': set(),
                'rewardAddresses': set(),
                'weight': 0,
                'delegatorWeight': 0,
                'totalWeight': 0,
                'validators': [],  # Keep individual validator data
                'countries': Counter(),
                'asns': Counter(),
                'cities': Counter(),
                'versions': Counter(),
            }
        g = groups[key]
        vid = v.get('id', '')
        g['id'].add(vid if isinstance(vid, str) else str(vid))
        g['rewardAddresses'].update(v.get('rewardAddresses', []))
        g['weight'] += v.get('weight', 0)
        g['delegatorWeight'] += v.get('delegatorWeight', v.get('delegatedWeight', 0))
        g['totalWeight'] += v.get('totalWeight', 0)
        g['validators'].append(v)

        # Extract GeoIP data
        geo = v.get('geo', {})
        country = geo.get('country', {})
        if country.get('code'):
            g['countries'][country['code']] += 1
        asnum = geo.get('asnum', {})
        if asnum.get('name'):
            g['asns'][asnum['name']] += 1
        city = geo.get('city', {})
        if city.get('name'):
            g['cities'][f"{city['name']}, {city.get('region', '')}"] += 1
        if v.get('version'):
            g['versions'][v['version']] += 1

    return list(groups.values())

def get_nakamoto_set(entities: List[Dict], threshold: float = 0.30) -> List[Dict]:
    """Get the minimum set of entities controlling >= threshold of stake"""
    total = sum(e['totalWeight'] for e in entities)
    sorted_entities = sorted(entities, key=lambda e: e['totalWeight'], reverse=True)

    cumsum = 0
    target = total * threshold
    nakamoto_set = []

    for e in sorted_entities:
        nakamoto_set.append(e)
        cumsum += e['totalWeight']
        if cumsum >= target:
            break

    return nakamoto_set

def analyze_nakamoto_set(date_str: str) -> Dict:
    """Analyze the Nakamoto-30 set for a given date"""
    validators = load_validators_ext(date_str)
    if not validators:
        return None

    entities = by_address_ext(validators)
    total_stake = sum(e['totalWeight'] for e in entities)
    nakamoto_set = get_nakamoto_set(entities, 0.30)

    # Aggregate stats for Nakamoto set
    n30_stake = sum(e['totalWeight'] for e in nakamoto_set)
    n30_validators = sum(len(e['validators']) for e in nakamoto_set)

    # Country distribution
    country_counts = Counter()
    asn_counts = Counter()
    for e in nakamoto_set:
        country_counts.update(e['countries'])
        asn_counts.update(e['asns'])

    # Unique countries and ASNs in Nakamoto set
    n30_countries = set()
    n30_asns = set()
    for e in nakamoto_set:
        n30_countries.update(e['countries'].keys())
        n30_asns.update(e['asns'].keys())

    # Get top reward addresses (anonymized/truncated for display)
    top_addresses = []
    for e in nakamoto_set:
        addrs = list(e['rewardAddresses'])
        if addrs:
            addr = addrs[0]
            # Truncate for privacy: P-avax1abc...xyz
            short = addr[:12] + '...' + addr[-4:] if len(addr) > 20 else addr
            top_addresses.append({
                'address': short,
                'full_address': addr,
                'stake_pct': e['totalWeight'] / total_stake * 100,
                'num_validators': len(e['validators']),
                'countries': dict(e['countries']),
                'asns': dict(e['asns']),
            })

    return {
        'date': date_str,
        'total_entities': len(entities),
        'total_validators': len(validators),
        'total_stake': total_stake,
        'n30_count': len(nakamoto_set),
        'n30_stake': n30_stake,
        'n30_stake_pct': n30_stake / total_stake * 100,
        'n30_validators': n30_validators,
        'n30_countries': len(n30_countries),
        'n30_asns': len(n30_asns),
        'country_distribution': dict(country_counts.most_common(10)),
        'asn_distribution': dict(asn_counts.most_common(10)),
        'top_entities': top_addresses,
    }

def analyze_all_quarterly() -> List[Dict]:
    """Analyze Nakamoto-30 set for all quarterly dates"""
    dates = get_quarterly_dates()
    results = []

    for d in dates:
        print(f"Analyzing {d}...")
        result = analyze_nakamoto_set(d)
        if result:
            results.append(result)

    return results

def print_detailed_report(results: List[Dict]):
    """Print detailed analysis report"""
    print()
    print("=" * 100)
    print("NAKAMOTO-30 SET ANALYSIS - Entities Controlling 30% of Avalanche Stake")
    print("=" * 100)
    print()

    # Summary table
    print("QUARTERLY OVERVIEW")
    print("-" * 100)
    print(f"{'Quarter':<10} {'Date':<12} {'N30 Entities':>12} {'N30 Validators':>14} {'Countries':>10} {'ASNs':>8} {'Stake %':>10}")
    print("-" * 100)

    for r in results:
        dt = datetime.strptime(r['date'], '%Y-%m-%d')
        quarter = f"{dt.year}Q{(dt.month-1)//3+1}"
        print(f"{quarter:<10} {r['date']:<12} {r['n30_count']:>12} {r['n30_validators']:>14} "
              f"{r['n30_countries']:>10} {r['n30_asns']:>8} {r['n30_stake_pct']:>9.1f}%")

    print("-" * 100)
    print()

    # Latest detailed breakdown
    latest = results[-1]
    print(f"DETAILED BREAKDOWN - {latest['date']}")
    print("-" * 100)
    print()
    print(f"Nakamoto-30 Set: {latest['n30_count']} entities control {latest['n30_stake_pct']:.1f}% of stake")
    print(f"These {latest['n30_count']} entities operate {latest['n30_validators']} validators")
    print()

    print("TOP ENTITIES BY STAKE:")
    print(f"{'Rank':<6} {'Address':<24} {'Stake %':>10} {'Validators':>12} {'Countries':>12}")
    print("-" * 70)
    for i, e in enumerate(latest['top_entities'], 1):
        countries = ', '.join(e['countries'].keys()) if e['countries'] else 'Unknown'
        print(f"{i:<6} {e['address']:<24} {e['stake_pct']:>9.2f}% {e['num_validators']:>12} {countries:>12}")
    print()

    print("COUNTRY DISTRIBUTION (validators in N30 set):")
    for country, count in sorted(latest['country_distribution'].items(), key=lambda x: -x[1]):
        print(f"  {country}: {count} validators")
    print()

    print("ASN/HOSTING DISTRIBUTION (validators in N30 set):")
    for asn, count in sorted(latest['asn_distribution'].items(), key=lambda x: -x[1])[:10]:
        print(f"  {asn}: {count} validators")
    print()

def track_entity_persistence(results: List[Dict]) -> Dict:
    """Track how long entities stay in Nakamoto-30 set"""
    # Track full addresses across time
    entity_appearances = defaultdict(list)

    for r in results:
        date = r['date']
        for e in r['top_entities']:
            entity_appearances[e['full_address']].append(date)

    # Categorize by persistence
    persistent = []  # In set for > 50% of observations
    occasional = []  # In set for 25-50%
    transient = []   # In set for < 25%

    total_periods = len(results)
    for addr, dates in entity_appearances.items():
        pct = len(dates) / total_periods * 100
        entry = {'address': addr[:12] + '...' + addr[-4:], 'appearances': len(dates), 'pct': pct}
        if pct > 50:
            persistent.append(entry)
        elif pct > 25:
            occasional.append(entry)
        else:
            transient.append(entry)

    return {
        'persistent': sorted(persistent, key=lambda x: -x['pct']),
        'occasional': sorted(occasional, key=lambda x: -x['pct']),
        'transient': sorted(transient, key=lambda x: -x['pct']),
        'total_unique': len(entity_appearances),
    }

def plot_nakamoto_geography(results: List[Dict]):
    """Plot geographic distribution over time"""
    dates = [datetime.strptime(r['date'], '%Y-%m-%d') for r in results]
    n30_countries = [r['n30_countries'] for r in results]
    n30_asns = [r['n30_asns'] for r in results]

    fig, (ax1, ax2) = pp.subplots(2, 1, figsize=(14, 10))

    # Countries over time
    ax1.plot(dates, n30_countries, 'o-', color='darkgreen', linewidth=2, markersize=6)
    ax1.set_ylabel('Unique Countries')
    ax1.set_title('Geographic Diversity of Nakamoto-30 Set Over Time', weight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0)

    # ASNs over time
    ax2.plot(dates, n30_asns, 's-', color='darkorange', linewidth=2, markersize=6)
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Unique ASNs (Hosting Providers)')
    ax2.set_title('Infrastructure Diversity of Nakamoto-30 Set Over Time', weight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(bottom=0)

    pp.tight_layout()
    pp.savefig(os.path.join(HIST_DIR, 'nakamoto_geography.svg'))
    pp.savefig(os.path.join(HIST_DIR, 'nakamoto_geography.png'), dpi=150)
    print("Saved nakamoto_geography.svg/png")

def plot_country_heatmap(results: List[Dict]):
    """Plot country distribution as stacked area"""
    # Get all countries that appear
    all_countries = set()
    for r in results:
        all_countries.update(r['country_distribution'].keys())

    # Get top 8 countries by total appearances
    country_totals = Counter()
    for r in results:
        country_totals.update(r['country_distribution'])
    top_countries = [c for c, _ in country_totals.most_common(8)]

    dates = [datetime.strptime(r['date'], '%Y-%m-%d') for r in results]

    # Build data matrix
    data = {c: [] for c in top_countries}
    data['Other'] = []

    for r in results:
        dist = r['country_distribution']
        other = 0
        for c in top_countries:
            data[c].append(dist.get(c, 0))
        for c, v in dist.items():
            if c not in top_countries:
                other += v
        data['Other'].append(other)

    fig, ax = pp.subplots(figsize=(14, 7))

    colors = pp.cm.tab10(np.linspace(0, 1, len(top_countries) + 1))

    bottom = np.zeros(len(dates))
    for i, (country, values) in enumerate(data.items()):
        ax.bar(dates, values, bottom=bottom, label=country, color=colors[i], width=60)
        bottom += np.array(values)

    ax.set_xlabel('Date')
    ax.set_ylabel('Number of Validators in N30 Set')
    ax.set_title('Country Distribution of Nakamoto-30 Validators Over Time', weight='bold')
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
    ax.grid(True, alpha=0.3, axis='y')

    pp.tight_layout()
    pp.savefig(os.path.join(HIST_DIR, 'nakamoto_countries.svg'))
    pp.savefig(os.path.join(HIST_DIR, 'nakamoto_countries.png'), dpi=150)
    print("Saved nakamoto_countries.svg/png")

def plot_asn_concentration(results: List[Dict]):
    """Plot ASN concentration over time"""
    dates = [datetime.strptime(r['date'], '%Y-%m-%d') for r in results]

    # Calculate HHI (Herfindahl-Hirschman Index) for ASN concentration
    hhi_values = []
    top_asn_share = []

    for r in results:
        dist = r['asn_distribution']
        total = sum(dist.values()) if dist else 1
        shares = [v/total for v in dist.values()]
        hhi = sum(s**2 for s in shares) * 10000  # Scale to 0-10000
        hhi_values.append(hhi)
        top_asn_share.append(max(dist.values()) / total * 100 if dist else 0)

    fig, (ax1, ax2) = pp.subplots(2, 1, figsize=(14, 10))

    ax1.plot(dates, hhi_values, 'o-', color='darkred', linewidth=2, markersize=6)
    ax1.set_ylabel('HHI Index')
    ax1.set_title('ASN Concentration (HHI) in Nakamoto-30 Set\n(Higher = more concentrated)', weight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=2500, color='orange', linestyle='--', alpha=0.7, label='Moderately concentrated (2500)')
    ax1.axhline(y=1500, color='green', linestyle='--', alpha=0.7, label='Unconcentrated (<1500)')
    ax1.legend()

    ax2.plot(dates, top_asn_share, 's-', color='purple', linewidth=2, markersize=6)
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Top ASN Share (%)')
    ax2.set_title('Share of Largest Hosting Provider in Nakamoto-30 Set', weight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 100)

    pp.tight_layout()
    pp.savefig(os.path.join(HIST_DIR, 'nakamoto_asn_concentration.svg'))
    pp.savefig(os.path.join(HIST_DIR, 'nakamoto_asn_concentration.png'), dpi=150)
    print("Saved nakamoto_asn_concentration.svg/png")

def write_nakamoto_summary(results: List[Dict], persistence: Dict):
    """Write detailed Nakamoto analysis summary"""
    latest = results[-1]

    # Find min/max values
    min_countries = min(results, key=lambda x: x['n30_countries'])
    max_countries = max(results, key=lambda x: x['n30_countries'])
    min_asns = min(results, key=lambda x: x['n30_asns'])
    max_asns = max(results, key=lambda x: x['n30_asns'])

    summary = f"""# Nakamoto-30 Set Deep Analysis

## Overview

Analysis of the entities that together control at least 30% of Avalanche's total stake,
using extended validator data with GeoIP metadata.

**Data Period**: {results[0]['date']} to {results[-1]['date']}
**Quarterly Snapshots**: {len(results)}

## Current State ({latest['date']})

| Metric | Value |
|--------|-------|
| Entities in N30 Set | {latest['n30_count']} |
| Validators Operated | {latest['n30_validators']} |
| Stake Controlled | {latest['n30_stake_pct']:.1f}% |
| Unique Countries | {latest['n30_countries']} |
| Unique ASNs | {latest['n30_asns']} |

## Geographic Diversity

| Metric | Current | Min | Max |
|--------|---------|-----|-----|
| Countries | {latest['n30_countries']} | {min_countries['n30_countries']} ({min_countries['date']}) | {max_countries['n30_countries']} ({max_countries['date']}) |
| ASNs | {latest['n30_asns']} | {min_asns['n30_asns']} ({min_asns['date']}) | {max_asns['n30_asns']} ({max_asns['date']}) |

## Current Top Entities

| Rank | Address | Stake % | Validators | Countries |
|------|---------|---------|------------|-----------|
"""

    for i, e in enumerate(latest['top_entities'], 1):
        countries = ', '.join(e['countries'].keys()) if e['countries'] else 'Unknown'
        summary += f"| {i} | `{e['address']}` | {e['stake_pct']:.2f}% | {e['num_validators']} | {countries} |\n"

    summary += f"""
## Country Distribution (Current)

| Country | Validators |
|---------|------------|
"""
    for country, count in sorted(latest['country_distribution'].items(), key=lambda x: -x[1]):
        summary += f"| {country} | {count} |\n"

    summary += f"""
## Hosting Provider Distribution (Current)

| Provider (ASN) | Validators |
|----------------|------------|
"""
    for asn, count in sorted(latest['asn_distribution'].items(), key=lambda x: -x[1])[:10]:
        summary += f"| {asn} | {count} |\n"

    summary += f"""
## Entity Persistence Analysis

How long do entities stay in the Nakamoto-30 set?

**Total unique entities ever in N30**: {persistence['total_unique']}

### Persistent Entities (>50% of time in N30)
"""
    if persistence['persistent']:
        for e in persistence['persistent'][:10]:
            summary += f"- `{e['address']}`: {e['appearances']}/{len(results)} quarters ({e['pct']:.0f}%)\n"
    else:
        summary += "None\n"

    summary += f"""
### Occasional Entities (25-50% of time in N30)
"""
    if persistence['occasional']:
        for e in persistence['occasional'][:10]:
            summary += f"- `{e['address']}`: {e['appearances']}/{len(results)} quarters ({e['pct']:.0f}%)\n"
    else:
        summary += "None\n"

    summary += f"""
### Transient Entities (<25% of time in N30)

{len(persistence['transient'])} entities appeared briefly in the N30 set.

## Plots

- [Geographic Diversity](nakamoto_geography.png)
- [Country Distribution](nakamoto_countries.png)
- [ASN Concentration](nakamoto_asn_concentration.png)

## Key Findings

1. **Geographic Concentration**: The N30 set spans {latest['n30_countries']} countries
2. **Infrastructure Risk**: {latest['n30_asns']} unique hosting providers
3. **Entity Churn**: {persistence['total_unique']} unique entities have been in N30 over time
4. **Persistence**: {len(persistence['persistent'])} entities consistently control significant stake
"""

    with open(os.path.join(HIST_DIR, 'NAKAMOTO_ANALYSIS.md'), 'w') as f:
        f.write(summary)
    print("Saved NAKAMOTO_ANALYSIS.md")

def save_detailed_csv(results: List[Dict]):
    """Save detailed quarterly data to CSV"""
    import csv

    with open(os.path.join(HIST_DIR, 'nakamoto_quarterly.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'n30_entities', 'n30_validators', 'n30_stake_pct',
                        'n30_countries', 'n30_asns', 'top_country', 'top_asn'])
        for r in results:
            top_country = max(r['country_distribution'].items(), key=lambda x: x[1])[0] if r['country_distribution'] else ''
            top_asn = max(r['asn_distribution'].items(), key=lambda x: x[1])[0] if r['asn_distribution'] else ''
            writer.writerow([
                r['date'], r['n30_count'], r['n30_validators'],
                f"{r['n30_stake_pct']:.2f}", r['n30_countries'], r['n30_asns'],
                top_country, top_asn
            ])
    print("Saved nakamoto_quarterly.csv")

###############################################################################

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("Analyzing Nakamoto-30 set over time...")
    results = analyze_all_quarterly()

    if not results:
        print("No data found!")
        exit(1)

    print_detailed_report(results)

    print("\nTracking entity persistence...")
    persistence = track_entity_persistence(results)

    print(f"\nEntity Persistence Summary:")
    print(f"  Total unique entities ever in N30: {persistence['total_unique']}")
    print(f"  Persistent (>50% of time): {len(persistence['persistent'])}")
    print(f"  Occasional (25-50%): {len(persistence['occasional'])}")
    print(f"  Transient (<25%): {len(persistence['transient'])}")

    print("\nGenerating plots...")
    plot_nakamoto_geography(results)
    plot_country_heatmap(results)
    plot_asn_concentration(results)

    print("\nWriting reports...")
    write_nakamoto_summary(results, persistence)
    save_detailed_csv(results)

    print("\nDone!")
