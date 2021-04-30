#!/usr/bin/env python
###############################################################################

import argparse
import json
import matplotlib.pyplot as pp
import numpy as np
import os
import re

from datetime import date
from typing import List, Dict, Tuple, Any
from numpy.random import default_rng as prng

###############################################################################
###############################################################################

def load(data_path: str) -> Tuple[np.array, np.array]:
    """validator weights and total weights (i.e. excl./incl. delegations)"""
    ts = [] ## validator weight incl. delegators
    ws = [] ## validator weight excl. delegators

    if args.extended:
        pattern = r'validators-ext(.[0-9]+)?.json$'
    else:
        pattern = r'validators(.[0-9]+)?.json$'

    for p, dns, fns in os.walk(os.path.normpath(data_path)):
        for fn in filter(lambda n: re.match(pattern, n), fns):
            with open(os.path.join(p, fn)) as file:
                validators = json.load(file)
            if args.group:
                validators = by_address(validators)

            ts.extend(map(lambda v: v['totalWeight'], validators))
            ws.extend(map(lambda v: v['weight'], validators))

    if args.gini_00:
        ts = gini_00(ts)['pdf_normed']
    elif args.gini_33:
        ts = gini_33(ts)['pdf_normed']
    elif args.gini_66:
        ts = gini_66(ts)['pdf_normed']
    else:
        ts = np.array(ts, dtype=np.float64)
        ts_exp = ts**args.exponent
        ts = ts_exp/np.max(ts_exp)*np.max(ts)

    if args.gini_00:
        ws = gini_00(ws)['pdf_normed']
    elif args.gini_33:
        ws = gini_33(ws)['pdf_normed']
    elif args.gini_66:
        ws = gini_66(ws)['pdf_normed']
    else:
        ws = np.array(ws, dtype=np.float64)
        ws_exp = ws**args.exponent
        ws = ws_exp/np.max(ws_exp)*np.max(ws)

    return np.sort(ts), np.sort(ws)

def by_address(validators: List[Any], groups={}) -> List[Any]:
    """groups validators by reward-addresses"""
    for k, v in map(
        lambda v: (frozenset(v['rewardAddresses']), v), validators
    ):
        g = groups.get(k, {
            'id': set(),
            'rewardAddresses': set(),
            'weight': 0,
            'delegatedWeight': 0,
            'totalWeight': 0
        })
        g['id'].update(v['id'] if type(v['id']) == list else [v['id']])
        g['rewardAddresses'].update(v['rewardAddresses'])
        g['weight'] += v['weight']
        g['delegatedWeight'] += v['delegatedWeight']
        g['totalWeight'] += v['totalWeight']
        groups[k] = g

    return groups.values()

def load_cum(data_path: str) -> Tuple[
        np.array, np.array, np.array, np.array
    ]:
    """validator (cum.) weights and (cum.) total weights"""
    ts, ws = load(data_path) ## load total weights & weights
    cts = np.cumsum(ts) ## cum. weight incl. delegators
    cws = np.cumsum(ws) ## cum. weight excl. delegators
    return ts, cts, ws, cws

def gini(a: np.array) -> np.float64:
    """gini coefficient of inequality"""
    # mean absolute difference
    mad = np.abs(np.subtract.outer(a, a)).mean()
    # mean absolute difference (relative) * 0.5
    return mad/np.mean(a)*0.5

def gini_pct(a: np.array) -> np.float64:
    """gini coefficient of inequality in percentages"""
    return 100*gini(a)

def gini_00(a: np.array) -> Dict[str, np.array]:
    """perfectly equal distribution with GINI=00.0%"""
    eql_a = np.ones(np.size(a))/np.size(a)
    eql_a /= np.max(eql_a) ## normed
    cum_a = np.cumsum(eql_a)
    return {
        'pdf': eql_a,
        'pdf_normed': eql_a/np.sum(eql_a)*np.sum(a),
        'cdf_normed': cum_a/np.max(cum_a)*np.max(a),
    }

def gini_33(a: np.array) -> Dict[str, np.array]:
    """uniformly random distribution with GINI=33.3%"""
    random = prng(seed=args.seed if args.seed else None)
    uni_a = random.uniform(size=np.size(a))/np.size(a)
    uni_a /= np.max(uni_a) ## normed
    cum_a = np.cumsum(np.sort(uni_a))
    return {
        'pdf': uni_a,
        'pdf_normed': uni_a/np.sum(uni_a)*np.sum(a),
        'cdf_normed': cum_a/np.max(cum_a)*np.max(a),
    }

def gini_66(a: np.array) -> Dict[str, np.array]:
    """log-logistic distribution with GINI=66.6%"""
    pdf_a = lambda b: lambda a: b*np.power(a, b-1)/np.power(1+np.power(a, b), 2)
    random = prng(seed=args.seed if args.seed else None)
    uni_a = random.uniform(size=np.size(a))/np.size(a)
    log_a = pdf_a(5)(np.sort(uni_a))
    log_a /= np.max(log_a) ## normed
    cum_a = np.cumsum(log_a)
    return {
        'pdf': log_a,
        'pdf_normed': log_a/np.sum(log_a)*np.sum(a),
        'cdf_normed': cum_a/np.max(cum_a)*np.max(a),
    }

def rotation(a: np.array, at: np.float64, delta=10) -> np.float64:
    """degree of rotation in screen coordinates"""
 ## return np.rad2deg(np.arctan2(a[at+delta] - a[at-delta], 2*delta))
    return 12.5

def sub_directory(path: str, index=-1) -> str:
    """(by default last) sub-directory beneath a given path"""
    sub_directory = sorted(next(os.walk(path))[1])[index]
    sub_directory = os.path.join(path, sub_directory)
    return os.path.normpath(sub_directory)

def plot_distribution(path: str):
    """plot (cum.) validator stake distribution"""
    path = os.path.normpath(path) if path else sub_directory('./json')
    ts, cts, ws, cws = load_cum(path) ## weights & total weights
    a_date = date.fromisoformat(path.split('/').pop())

    cts_g00, ccts_g00 = [gini_00(cts)[n] for n in ('pdf', 'cdf_normed')]
    cts_g33, ccts_g33 = [gini_33(cts)[n] for n in ('pdf', 'cdf_normed')]
    cts_g66, ccts_g66 = [gini_66(cts)[n] for n in ('pdf', 'cdf_normed')]

    quorum_pct1 = 0.70 ## 14 of 20 peers sampled
    quorum_ctr1 = np.max(cts) * (1.00 - quorum_pct1)
    quorum_idx1 = cts.size - np.sum(cts > quorum_ctr1)

    quorum_pct2 = 0.30 ## for annotation only!
    quorum_ctr2 = np.max(cts) * (1.00 - quorum_pct2)
    quorum_idx2 = cts.size - np.sum(cts > quorum_ctr2)

    quorum_pct3 = 0.25 ## for annotation only!
    quorum_ctr3 = np.max(cts) * (1.00 - quorum_pct3)
    quorum_idx3 = cts.size - np.sum(cts > quorum_ctr3)

    pp.figure(figsize=(21.5, 9.0))

    ###########################################################################
    ax = pp.subplot(3, 1, (1,2))
    ###########################################################################

    pp.title(f'(Cumulative) Stake Distribution of Avalanche Validators [{a_date}]', weight='bold')
    pp.ylabel('Cum. Stake [{:.1f}M $AVAX]'.format(np.max(cts)/1e15))
    pp.xlim(0, cts.size)
    pp.ylim(0, np.max(cts))

    ax.fill_between(
        np.arange(cts.size), cts, color='lightcoral')
    ax.plot(
        np.arange(cts.size), cts, color='darkred', linestyle='-', linewidth=2, zorder=3,
        label='cum. stake of validators incl. delegations (GINI={:04.1f}%)'.format(gini_pct(ts)))
    ax.fill_between(
        np.arange(cws.size), cws, color='lightblue')
    ax.plot(
        np.arange(cws.size), cws, color='darkblue', linestyle='-', linewidth=2,
        label='cum. stake of validators excl. delegations (GINI={:04.1f}%)'.format(gini_pct(ws)))

    ax.plot(
        np.arange(ts.size), ccts_g66, color='black', linestyle=':', linewidth=1)
    ax.plot(
        np.arange(ts.size), ccts_g33, color='black', linestyle=':', linewidth=1)
    ax.plot(
        np.arange(ts.size), ccts_g00, color='black', linestyle=':', linewidth=1)

    at = int(np.round(cts.size*2/3))
    pp.annotate(
        'GINI={:.1f}%'.format(gini_pct(cts_g66)), (at, ccts_g66[at]),
        bbox=dict(boxstyle='round', fc='white', lw=0), weight='bold',
        fontsize=8, rotation=rotation(ccts_g66, at))

    at = int(np.round(ts.size*1/2))
    pp.annotate(
        'GINI={:.1f}%'.format(gini_pct(cts_g33)), (at, ccts_g33[at]),
        bbox=dict(boxstyle='round', fc='white', lw=0), weight='bold',
        fontsize=8, rotation=rotation(ccts_g33, at))

    at = int(np.round(cts.size*1/3))
    pp.annotate(
        'GINI={:.1f}%'.format(gini_pct(cts_g00)), (at, ccts_g00[at]),
        bbox=dict(boxstyle='round', fc='white', lw=0), weight='bold',
        fontsize=8, rotation=rotation(ccts_g00, at))

    if not args.gini_33:

        pp.scatter(
            quorum_idx1, quorum_ctr1, color='black', zorder=10, s=36)
        pp.scatter(
            quorum_idx1, quorum_ctr1, color='white', zorder=11, s=8)
        pp.annotate(
            '({:.0f}, {:.1f}M)'.format(quorum_idx1, quorum_ctr1/1e15),
            (quorum_idx1, quorum_ctr1), weight='bold', color='white', fontsize=9,
            xytext=(-5, -2), ha='center', va='top', textcoords='offset points', rotation=90)
        pp.annotate(
            '({:.0f}, {:.1f}M)'.format(quorum_idx1, quorum_ctr1/1e15),
            (quorum_idx1, quorum_ctr1), weight='bold', color='black', fontsize=9,
            xytext=(-6, -1), ha='center', va='top', textcoords='offset points', rotation=90)

        pp.scatter(
            quorum_idx2, quorum_ctr2, color='black', zorder=10, s=36)
        pp.scatter(
            quorum_idx2, quorum_ctr2, color='white', zorder=11, s=8)
        pp.annotate(
            '({:.0f}, {:.1f}M)'.format(quorum_idx2, quorum_ctr2/1e15),
            (quorum_idx2, quorum_ctr2), weight='bold', color='white', fontsize=9,
            xytext=(-5, -2), ha='center', va='top', textcoords='offset points', rotation=90)
        pp.annotate(
            '({:.0f}, {:.1f}M)'.format(quorum_idx2, quorum_ctr2/1e15),
            (quorum_idx2, quorum_ctr2), weight='bold', color='black', fontsize=9,
            xytext=(-6, -1), ha='center', va='top', textcoords='offset points', rotation=90)

    ax.axvline(
        x=quorum_idx1, label='30%-vs-70% split: LHS controls 30% & RHS 70%',
        color='black', linestyle='-.', linewidth=2)
    ax.axvline(
        x=quorum_idx2, label='70%-vs-30% split: LHS controls 70% & RHS 30%',
        color='black', linestyle='-.', linewidth=2)
    pp.annotate(
        'GINI={:.1f}%'.format(gini_pct(ts)), (quorum_idx3, quorum_ctr3),
        bbox=dict(boxstyle='rarrow', fc='lightcoral', ec='darkred', alpha=0.9, lw=2),
        xytext=(-28, 0), weight='bold', color='darkred', fontsize=28,
        ha='right', va='center', textcoords='offset points')

    ax.set_xticks(np.arange(0, cts.size, 50), minor=True)
    ax.yaxis.set_major_formatter(pp.FuncFormatter(
        lambda n, _: '{:.0f}M'.format(n/1e15)
    ))

    ax.grid(which='major', axis='y')
    ax.legend(loc='upper left')

    ###########################################################################
    ax = pp.subplot(3, 1, (3,3))
    ###########################################################################

    if not args.group:
        pp.xlabel('Validators [{:d}]'.format(cts.size))
    else:
        pp.xlabel('Validators by Reward Address [{:d}]'.format(cts.size))

    pp.ylabel('Stake [$AVAX]')
    pp.xlim(0, ts.size)
    pp.ylim(0, np.max(ts))

    ax.fill_between(
        np.arange(ts.size), ts, color='lightcoral')
    ax.plot(
        np.arange(ts.size), ts, color='darkred', linestyle='-', linewidth=2, zorder=3,
        label='stake of validators incl. delegations (GINI={:04.1f}%)'.format(gini_pct(ts)))
    ax.fill_between(
        np.arange(ws.size), ws, color='lightblue')
    ax.plot(
        np.arange(ws.size), ws, color='darkblue', linestyle='-', linewidth=2,
        label='stake of validators excl. delegations (GINI={:04.1f}%)'.format(gini_pct(ws)))
    ax.axvline(
        x=quorum_idx1, color='black', linestyle='-.', linewidth=2)
    ax.axvline(
        x=quorum_idx2, color='black', linestyle='-.', linewidth=2)

    ax.set_xticks(np.arange(0, ts.size, 50), minor=True)
    ax.yaxis.set_major_formatter(pp.FuncFormatter(
        lambda n, _: '{:.2f}M'.format(n/1e15)
    ))

    ax.grid(which='major', axis='y')
    ax.legend(loc='upper left')

    if args.group:
        pp.savefig(f'image/{a_date}G.svg')
    else:
        pp.savefig(f'image/{a_date}.svg')

    if args.show:
        pp.show()

###############################################################################
###############################################################################

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Plots Avalanche stake distribution')
    parser.add_argument('data_path', type=str, nargs='?',
        help='path to validator data (default: %(default)s)', default=None)
    parser.add_argument('--seed', type=int,
        help='random generator seed (default: %(default)s)', default=1)
    parser.add_argument('--gini-00', action='store_true',
        help='plot equal distribution (default: %(default)s)', default=False)
    parser.add_argument('--gini-33', action='store_true',
        help='plot uniform distribution (default: %(default)s)', default=False)
    parser.add_argument('--gini-66', action='store_true',
        help='plot log-logistic distribution (default: %(default)s)', default=False)
    parser.add_argument('-g', '--group', action='store_true',
        help='group by reward address (default: %(default)s)', default=False)
    parser.add_argument('-e', '--extended', action='store_true',
        help='use extended validators (default: %(default)s)', default=False)
    parser.add_argument('-x', '--exponent', type=float,
        help='distribution exponent mapper (default: %(default)s)', default=1.0)
    parser.add_argument('-s', '--show', action='store_true',
        help='show plot (default: %(default)s)', default=False)

    args = parser.parse_args()
    plot_distribution(args.data_path)

###############################################################################
###############################################################################
