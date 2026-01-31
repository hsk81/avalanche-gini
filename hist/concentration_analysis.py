#!/usr/bin/env python
###############################################################################
# Concentration Analysis - Is Nakamoto-30 an upper bound?
# Investigates whether "different entities" might actually be the same operator
###############################################################################

import json
import os
from collections import Counter, defaultdict
from typing import List, Dict

JSON_DIR = '../json'
DATE = '2026-01-31'

def load_validators_ext(date_str: str) -> List[Dict]:
    path = os.path.join(JSON_DIR, date_str, 'validators-ext.json')
    with open(path) as f:
        return json.load(f)

def by_address_ext(validators: List[Dict]) -> List[Dict]:
    """Group validators by reward address with full metadata"""
    groups = {}
    for v in validators:
        key = frozenset(v.get('rewardAddresses', []))
        if not key:
            continue
        if key not in groups:
            groups[key] = {
                'rewardAddresses': list(v.get('rewardAddresses', [])),
                'weight': 0,
                'totalWeight': 0,
                'validators': [],
                'asns': set(),
                'countries': set(),
                'ips': set(),
                'versions': set(),
            }
        g = groups[key]
        g['weight'] += v.get('weight', 0)
        g['totalWeight'] += v.get('totalWeight', 0)
        g['validators'].append(v)

        geo = v.get('geo', {})
        asn = geo.get('asnum', {}).get('name', '')
        country = geo.get('country', {}).get('code', '')
        if asn:
            g['asns'].add(asn)
        if country:
            g['countries'].add(country)
        if v.get('ip'):
            g['ips'].add(v['ip'].split(':')[0])  # Just IP, no port
        if v.get('version'):
            g['versions'].add(v['version'])

    return sorted(groups.values(), key=lambda x: -x['totalWeight'])

def get_nakamoto_set(entities: List[Dict], threshold: float = 0.30) -> List[Dict]:
    total = sum(e['totalWeight'] for e in entities)
    cumsum = 0
    target = total * threshold
    result = []
    for e in entities:
        result.append(e)
        cumsum += e['totalWeight']
        if cumsum >= target:
            break
    return result

def analyze_concentration():
    validators = load_validators_ext(DATE)
    entities = by_address_ext(validators)
    total_stake = sum(e['totalWeight'] for e in entities)
    n30 = get_nakamoto_set(entities, 0.30)

    print("=" * 90)
    print("CONCENTRATION ANALYSIS - Is Nakamoto-30 an Upper Bound?")
    print("=" * 90)
    print(f"\nDate: {DATE}")
    print(f"Nakamoto-30 entities: {len(n30)}")
    print()

    # 1. ASN Overlap Analysis
    print("=" * 90)
    print("1. ASN (HOSTING PROVIDER) OVERLAP")
    print("=" * 90)
    print("If multiple 'entities' share the same hosting provider, they could be:")
    print("  - The same operator using different reward addresses")
    print("  - Subject to the same infrastructure risks/censorship")
    print()

    asn_to_entities = defaultdict(list)
    for i, e in enumerate(n30):
        for asn in e['asns']:
            asn_to_entities[asn].append(i + 1)

    print(f"{'ASN':<45} {'Entities Sharing':>20}")
    print("-" * 70)
    for asn, entity_ranks in sorted(asn_to_entities.items(), key=lambda x: -len(x[1])):
        if len(entity_ranks) > 1:
            print(f"{asn:<45} {str(entity_ranks):>20}")

    # Count entities that share ASN with another N30 entity
    entities_sharing_asn = set()
    for asn, ranks in asn_to_entities.items():
        if len(ranks) > 1:
            entities_sharing_asn.update(ranks)

    print()
    print(f"Entities sharing ASN with another N30 entity: {len(entities_sharing_asn)}/{len(n30)}")

    # 2. IP Subnet Analysis
    print()
    print("=" * 90)
    print("2. IP SUBNET ANALYSIS")
    print("=" * 90)
    print("Validators in same /24 subnet suggest same operator or datacenter")
    print()

    subnet_to_entities = defaultdict(list)
    for i, e in enumerate(n30):
        for ip in e['ips']:
            subnet = '.'.join(ip.split('.')[:3])  # /24 subnet
            subnet_to_entities[subnet].append((i + 1, ip))

    shared_subnets = {k: v for k, v in subnet_to_entities.items() if len(v) > 1}
    if shared_subnets:
        print(f"{'Subnet':<20} {'Entities & IPs'}")
        print("-" * 70)
        for subnet, entries in sorted(shared_subnets.items(), key=lambda x: -len(x[1])):
            entities = set(e[0] for e in entries)
            if len(entities) > 1:  # Different entities in same subnet
                print(f"{subnet}.0/24: Entities {sorted(entities)}")
    else:
        print("No different entities share IP subnets")

    # 3. Entity Details
    print()
    print("=" * 90)
    print("3. DETAILED ENTITY BREAKDOWN")
    print("=" * 90)
    print()

    for i, e in enumerate(n30, 1):
        stake_pct = e['totalWeight'] / total_stake * 100
        addr = e['rewardAddresses'][0] if e['rewardAddresses'] else 'Unknown'
        print(f"Entity #{i}: {addr[:20]}...{addr[-6:]}")
        print(f"  Stake: {stake_pct:.2f}% | Validators: {len(e['validators'])}")
        print(f"  Countries: {', '.join(sorted(e['countries'])) or 'Unknown'}")
        print(f"  ASNs: {', '.join(sorted(e['asns'])) or 'Unknown'}")
        print(f"  Versions: {', '.join(sorted(e['versions'])) or 'Unknown'}")
        print()

    # 4. Concentration by ASN
    print("=" * 90)
    print("4. STAKE CONCENTRATION BY HOSTING PROVIDER")
    print("=" * 90)
    print("If a hosting provider is compromised/coerced, how much stake is at risk?")
    print()

    # For N30 validators, sum stake by ASN
    asn_stake = defaultdict(int)
    asn_validators = defaultdict(int)
    for e in n30:
        stake_per_validator = e['totalWeight'] / len(e['validators']) if e['validators'] else 0
        for v in e['validators']:
            asn = v.get('geo', {}).get('asnum', {}).get('name', 'Unknown')
            asn_stake[asn] += stake_per_validator
            asn_validators[asn] += 1

    n30_stake = sum(e['totalWeight'] for e in n30)
    print(f"{'ASN':<45} {'Validators':>10} {'Stake %':>10}")
    print("-" * 70)
    for asn, stake in sorted(asn_stake.items(), key=lambda x: -x[1])[:10]:
        pct = stake / total_stake * 100
        print(f"{asn:<45} {asn_validators[asn]:>10} {pct:>9.2f}%")

    # 5. Country Concentration
    print()
    print("=" * 90)
    print("5. STAKE CONCENTRATION BY COUNTRY (Regulatory Risk)")
    print("=" * 90)
    print("If a country mandates censorship, how much stake could be affected?")
    print()

    country_stake = defaultdict(int)
    country_validators = defaultdict(int)
    for e in n30:
        stake_per_validator = e['totalWeight'] / len(e['validators']) if e['validators'] else 0
        for v in e['validators']:
            country = v.get('geo', {}).get('country', {}).get('code', 'Unknown')
            country_stake[country] += stake_per_validator
            country_validators[country] += 1

    print(f"{'Country':<20} {'Validators':>10} {'Stake %':>10}")
    print("-" * 45)
    for country, stake in sorted(country_stake.items(), key=lambda x: -x[1]):
        pct = stake / total_stake * 100
        print(f"{country:<20} {country_validators[country]:>10} {pct:>9.2f}%")

    # 6. Effective Nakamoto Estimates
    print()
    print("=" * 90)
    print("6. EFFECTIVE NAKAMOTO COEFFICIENT ESTIMATES")
    print("=" * 90)
    print()

    print(f"UPPER BOUND (by reward address):     {len(n30)} entities")
    print()

    # By ASN - if each unique ASN is one "controller"
    asn_weights = defaultdict(int)
    for e in entities:
        # Assign entity's stake to its primary ASN
        asn_set = e.get('asns', set())
        if asn_set and isinstance(asn_set, set) and len(asn_set) > 0:
            validators = e.get('validators', [])
            if validators:
                primary_asn = max(asn_set, key=lambda a: sum(1 for v in validators
                    if v.get('geo', {}).get('asnum', {}).get('name') == a))
            else:
                primary_asn = list(asn_set)[0]
            asn_weights[primary_asn] += e['totalWeight']
        else:
            asn_weights['Unknown'] += e['totalWeight']

    sorted_asns = sorted(asn_weights.items(), key=lambda x: -x[1])
    cumsum = 0
    n30_by_asn = 0
    for asn, weight in sorted_asns:
        cumsum += weight
        n30_by_asn += 1
        if cumsum >= total_stake * 0.30:
            break

    print(f"BY HOSTING PROVIDER (ASN):           {n30_by_asn} providers")
    print("  (Assumes provider could control/coerce all hosted validators)")
    print()

    # By Country
    country_weights = defaultdict(int)
    for e in entities:
        country_set = e.get('countries', set())
        validators = e.get('validators', [])
        if country_set and isinstance(country_set, set) and len(country_set) > 0 and validators:
            # Weight by validators in each country
            for v in validators:
                country = v.get('geo', {}).get('country', {}).get('code', 'Unknown')
                country_weights[country] += e['totalWeight'] / len(validators)
        else:
            country_weights['Unknown'] += e['totalWeight']

    sorted_countries = sorted(country_weights.items(), key=lambda x: -x[1])
    cumsum = 0
    n30_by_country = 0
    for country, weight in sorted_countries:
        cumsum += weight
        n30_by_country += 1
        if cumsum >= total_stake * 0.30:
            break

    print(f"BY COUNTRY (regulatory risk):        {n30_by_country} countries")
    print("  (Assumes government could mandate censorship of all local validators)")
    print()

    # Summary
    print("=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print()
    print("The Nakamoto-30 coefficient of 11 entities is an UPPER BOUND.")
    print()
    print("More realistic estimates depending on threat model:")
    print(f"  - Trust reward addresses (optimistic):  {len(n30)} entities")
    print(f"  - Trust hosting providers:              {n30_by_asn} providers")
    print(f"  - Trust national jurisdictions:         {n30_by_country} countries")
    print()
    print("The difference is significant if the threat model includes:")
    print("  - Infrastructure providers being compromised or coerced")
    print("  - Government-mandated censorship in key jurisdictions")
    print("  - Single operators using multiple reward addresses")
    print()

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    analyze_concentration()
