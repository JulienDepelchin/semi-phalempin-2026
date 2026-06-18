#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_stats.py — génère stats.json depuis l'API RaceResult
Course des 2 Stades Domitys, Villeneuve d'Ascq

Usage : python scripts/build_stats.py
Output: stats.json (à la racine du projet)
"""
import json, math, sys, requests

API_URL = "https://my2.raceresult.com/394765/results/list"
API_KEY = "2c7d5d00e72248cb9cade88d8c469a2b"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Paramètre f= pour chaque épreuve
RACES = {
    "10km": "10km\x0c<Ignore>\x0c<Ignore>",
    "6km":  "6km\x0c<Ignore>\x0c<Ignore>",
}

# ── Fetch ──────────────────────────────────────────────────────────────────

def fetch_race(f_param):
    params = {
        "key": API_KEY,
        "listname": "En ligne|Final",
        "contest": "0", "r": "all", "l": "0",
        "f": f_param,
    }
    r = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()["data"]
    key = next(iter(data))
    return data[key]

# ── Parsing ────────────────────────────────────────────────────────────────

def time_to_sec(t):
    """'31:51' → 1911   '1:01:30' → 3690"""
    try:
        p = t.strip().split(":")
        if len(p) == 2:
            return int(p[0]) * 60 + int(p[1])
        return int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])
    except Exception:
        return None

def parse_runners(rows):
    """
    Structure d'une ligne RaceResult :
    [id, dossard, position, nom, drapeau, annee, club, temps_gun, temps_chip, couleur]
    couleur = "C(88,14,249)" pour les femmes, "" pour les hommes
    """
    runners = []
    for row in rows:
        if len(row) < 8:
            continue
        t = time_to_sec(row[7])
        if t is None:
            continue
        couleur = (row[9].strip() if len(row) > 9 else "")
        genre = "F" if couleur.startswith("C(") else "M"
        runners.append({
            "dossard":   str(row[1]).strip(),
            "nom":       str(row[3]).strip(),
            "annee":     str(row[5]).strip() if len(row) > 5 else "",
            "club":      str(row[6]).strip() if len(row) > 6 else "",
            "temps_str": row[7].strip(),
            "temps_sec": t,
            "genre":     genre,
        })
    # Trier par temps, assigner la position officielle
    runners.sort(key=lambda r: r["temps_sec"])
    for i, r in enumerate(runners):
        r["pos"] = i + 1
    return runners

# ── Statistiques ───────────────────────────────────────────────────────────

def quantile(sorted_arr, p):
    if not sorted_arr:
        return 0
    idx = (len(sorted_arr) - 1) * p
    lo, hi = int(idx), min(int(idx) + 1, len(sorted_arr) - 1)
    return sorted_arr[lo] + (sorted_arr[hi] - sorted_arr[lo]) * (idx - lo)

def stats_from(times):
    if not times:
        return {}
    a = sorted(times)
    return {
        "n":          len(a),
        "medianTime": int(quantile(a, 0.50)),
        "p10":        int(quantile(a, 0.10)),
        "p25":        int(quantile(a, 0.25)),
        "p75":        int(quantile(a, 0.75)),
        "p90":        int(quantile(a, 0.90)),
        "fastest":    a[0],
        "slowest":    a[-1],
    }

def make_hist(times, lo, hi, bin_sec=30):
    n = max(1, math.ceil((hi - lo) / bin_sec))
    counts = [0] * n
    for t in times:
        if t < lo or t >= hi:
            continue
        counts[min(n - 1, math.floor((t - lo) / bin_sec))] += 1
    return counts

def rank_curve(times, max_pts=512):
    """Liste triée sous-échantillonnée pour le calcul de rang genre côté client."""
    a = sorted(times)
    if len(a) <= max_pts:
        return a
    step = len(a) / max_pts
    return [a[min(len(a) - 1, round(i * step))] for i in range(max_pts)]

# ── Main ───────────────────────────────────────────────────────────────────

output = {}

for label, f_param in RACES.items():
    print(f"Fetching {label}...", flush=True)
    rows = fetch_race(f_param)
    runners = parse_runners(rows)

    all_t = [r["temps_sec"] for r in runners]
    men_t = [r["temps_sec"] for r in runners if r["genre"] == "M"]
    wom_t = [r["temps_sec"] for r in runners if r["genre"] == "F"]

    a_sorted = sorted(all_t)
    # Domaine : 1er–99e centile pour écrêter les outliers
    lo = int((quantile(a_sorted, 0.01) // 30) * 30)
    hi = int((quantile(a_sorted, 0.99) // 30 + 1) * 30)

    g  = stats_from(all_t)
    gM = stats_from(men_t)
    gF = stats_from(wom_t)

    print(f"  {label}: {g['n']} finishers | médiane {g['medianTime']//60}:{g['medianTime']%60:02d} "
          f"| H:{len(men_t)} F:{len(wom_t)}")

    output[label] = {
        "global": g,
        "byGender": {"M": gM, "F": gF},
        "finishHist": {
            "domain":      [lo, hi],
            "binSec":      30,
            "men":         make_hist(men_t, lo, hi, 30),
            "women":       make_hist(wom_t, lo, hi, 30),
            "menMedian":   gM.get("medianTime"),
            "womenMedian": gF.get("medianTime"),
        },
        "genderRankCurve": {
            "M": {"size": len(men_t), "times": rank_curve(men_t)},
            "F": {"size": len(wom_t), "times": rank_curve(wom_t)},
        },
        "runners": runners,
    }

out_path = "stats.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

print(f"stats.json saved ({__import__('os').path.getsize(out_path)//1024} KB)")
