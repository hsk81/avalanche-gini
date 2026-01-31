# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository tracks and visualizes the stake distribution (GINI coefficient) of Avalanche validators over time. It fetches validator data from the Avalanche API, computes GINI inequality metrics, and generates cumulative stake distribution plots.

## Commands

### Full Pipeline (fetch + plot + commit)
```bash
./stakes.sh                                    # Fetches data, plots, and commits to git
./stakes.sh -a https://custom-api.example.com  # Use custom API endpoint
```

### Setup Virtual Environment
```bash
PY=3 ./setup.sh              # Initialize Python 3 virtualenv
source bin/activate          # Activate environment
pip install matplotlib numpy # Install dependencies
```

### Individual Operations
```bash
# Fetch validator data only (creates json/YYYY-MM-DD/ directory)
./json/validators-fetch.sh
./json/validators-fetch.sh -g  # With GeoIP lookup

# Plot stake distribution only (requires active virtualenv)
./stakes.py                    # Plot latest data
./stakes.py -g                 # Group validators by reward address
./stakes.py -s                 # Show plot interactively
./stakes.py json/2021-05-03    # Plot specific date

# List validators from JSON data
./json/validators-list.sh -g < ./json/$(date +'%Y-%m-%d')/validators-ext.json
```

## Architecture

### Data Flow
1. `stakes.sh` orchestrates: fetch -> plot -> git commit
2. `json/validators-fetch.sh` fetches from Avalanche P-Chain API (`platform.getCurrentValidators`) and peer info (`info.peers`), joining them by node ID
3. `stakes.py` loads JSON data, computes GINI coefficients, and generates SVG plots

### Data Storage
- `json/YYYY-MM-DD/validators.json` - Basic validator data (weight, delegatorWeight, totalWeight)
- `json/YYYY-MM-DD/validators-ext.json` - Extended data with GeoIP info
- `image/YYYY-MM-DD.svg` - Individual validator plot
- `image/YYYY-MM-DDG.svg` - Grouped by reward address plot

### Key Functions in stakes.py
- `load()` - Parses validator JSON, optionally groups by reward address
- `gini()` - Computes GINI coefficient using mean absolute difference
- `gini_00/33/66()` - Generate reference distributions (equal, uniform, log-logistic)
- `plot_distribution()` - Creates cumulative distribution plot with 30%/70% control lines

## Dependencies

System packages: `python3`, `jq`, `geoip`, `geoip-database`, `geoip-database-extra`
Python packages: `matplotlib`, `numpy`
