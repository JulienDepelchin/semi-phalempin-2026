#!/usr/bin/env python3
"""
build_stats.py — génère stats.json depuis le PDF de résultats
Semi-Marathon de Phalempin 2025

Usage : python scripts/build_stats.py <pdf_file>
Output: stats.json (à la racine du projet)

Format ligne PDF :
  1. 4052 PAQUET, Amaury M (1) SEM (1) SERAING AC 1:05:36 1:05:36
"""

import json, math, re, sys

# ── Configuration ──────────────────────────────────────────────────────────
RACE_LABEL = '21km'
BIN_SEC = 60

# Année représentative par catégorie FFA (utilisée par getCategory() côté JS)
# Choisie pour tomber dans le bon groupe d'âge dans CourseDansLaCourseSlide
CAT_YEAR: dict[str, int] = {
    'CA':  2010,  # Cadet(te)       born 2009-2010
    'JU':  2008,  # Junior          born 2007-2008
    'ES':  2005,  # Espoir          born 2004-2006
    'SE':  1997,  # Senior          born 1992-2003  → groupe ≃20-29
    'M0':  1989,  # Master 0        born 1987-1991  → groupe ≃30-39
    'M1':  1984,  # Master 1        born 1982-1986  → groupe ≃40-49
    'M2':  1979,  # Master 2        born 1977-1981  → groupe ≃40-49
    'M3':  1974,  # Master 3        born 1972-1976  → groupe ≃50-59
    'M4':  1969,  # Master 4        born 1967-1971  → groupe ≃50-59
    'M5':  1964,  # Master 5        born 1962-1966  → groupe ≃60-69
    'M6':  1959,  # Master 6        born 1957-1961  → groupe ≃60-69
    'M7':  1954,  # Master 7        born 1952-1956  → groupe ≃70+
    'M8':  1949,  # Master 8        born 1947-1951  → groupe ≃70+
    'M9':  1944,  # Master 9        born 1942-1946  → groupe ≃70+
    'M10': 1940,  # Master 10       born <1942      → groupe ≃70+
}

def cat_to_year(cat_raw: str) -> str:
    """'M1M' → '1984'   'SEF' → '1997'   'M10M' → '1940'   inconnu → ''"""
    base = re.sub(r'[MF]$', '', cat_raw).upper()
    return str(CAT_YEAR.get(base, ''))


# ── Parsing PDF ────────────────────────────────────────────────────────────

# Ligne type : 1. 4052 PAQUET, Amaury M (1) SEM (1) SERAING AC 215111 1:05:36 1:05:36
LINE_RE = re.compile(
    r'^\s*(\d+)\.\s+'                         # rang général
    r'(\d+)\s+'                               # dossard
    r'(.+?)\s+'                               # nom (non-greedy)
    r'([MF])\s+\((\d+)\)\s+'                # genre (rang_genre)
    r'([A-Z][A-Z0-9]*[MF])\s+\((\d+)\)\s+' # catégorie (rang_cat)
    r'(.*?)'                                  # club + éventuelle licence (peut être vide)
    r'(\d:\d{2}:\d{2})\s+'                   # temps officiel
    r'(\d:\d{2}:\d{2})\s*$'                  # temps réel (chip)
)

def time_to_sec(t: str) -> int:
    p = t.strip().split(':')
    if len(p) == 2:
        return int(p[0]) * 60 + int(p[1])
    return int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])

def clean_club(raw: str) -> str:
    """Supprime le numéro de licence FFA (5-7 chiffres) en fin de chaîne."""
    return re.sub(r'\s+\d{5,7}\s*$', '', raw).strip()

def parse_pdf(pdf_path: str) -> list[dict]:
    try:
        import pdfplumber
    except ImportError:
        print("Erreur : pdfplumber requis. Installez avec : pip install pdfplumber")
        sys.exit(1)

    runners: list[dict] = []
    seen: set[str] = set()

    with pdfplumber.open(pdf_path) as pdf:
        print(f"  PDF : {len(pdf.pages)} pages")
        for page in pdf.pages:
            text = page.extract_text() or ''
            for line in text.splitlines():
                m = LINE_RE.match(line)
                if not m:
                    continue
                rank, dossard, nom, genre, _, cat_raw, _, club_raw, tps_off, tps_reel = m.groups()

                dossard = dossard.strip()
                if dossard in seen:
                    continue
                seen.add(dossard)

                t = time_to_sec(tps_off)  # temps officiel pour le classement
                runners.append({
                    'dossard':   dossard,
                    'nom':       nom.strip(),
                    'annee':     cat_to_year(cat_raw),
                    'club':      clean_club(club_raw),
                    'temps_str': tps_off.strip(),
                    'temps_sec': t,
                    'genre':     genre,
                    'pos':       int(rank),
                })

    runners.sort(key=lambda r: r['temps_sec'])
    return runners


# ── Statistiques ───────────────────────────────────────────────────────────

def quantile(sorted_arr: list[int], p: float) -> float:
    if not sorted_arr:
        return 0.0
    idx = (len(sorted_arr) - 1) * p
    lo, hi = int(idx), min(int(idx) + 1, len(sorted_arr) - 1)
    return sorted_arr[lo] + (sorted_arr[hi] - sorted_arr[lo]) * (idx - lo)

def stats_from(times: list[int]) -> dict:
    if not times:
        return {}
    a = sorted(times)
    return {
        'n':          len(a),
        'medianTime': int(quantile(a, 0.50)),
        'p10':        int(quantile(a, 0.10)),
        'p25':        int(quantile(a, 0.25)),
        'p75':        int(quantile(a, 0.75)),
        'p90':        int(quantile(a, 0.90)),
        'fastest':    a[0],
        'slowest':    a[-1],
    }

def make_hist(times: list[int], lo: int, hi: int, bin_sec: int = BIN_SEC) -> list[int]:
    n = max(1, math.ceil((hi - lo) / bin_sec))
    counts = [0] * n
    for t in times:
        if t < lo or t >= hi:
            continue
        counts[min(n - 1, math.floor((t - lo) / bin_sec))] += 1
    return counts

def rank_curve(times: list[int], max_pts: int = 512) -> list[int]:
    """Liste triée sous-échantillonnée pour le calcul de rang genre côté client."""
    a = sorted(times)
    if len(a) <= max_pts:
        return a
    step = len(a) / max_pts
    return [a[min(len(a) - 1, round(i * step))] for i in range(max_pts)]


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(f"Usage : python {sys.argv[0]} <classement.pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    print(f"Parsing {pdf_path}...")
    runners = parse_pdf(pdf_path)

    if not runners:
        print("ERREUR : aucun coureur trouvé. Vérifiez le format du PDF.")
        sys.exit(1)

    all_t = [r['temps_sec'] for r in runners]
    men_t = [r['temps_sec'] for r in runners if r['genre'] == 'M']
    wom_t = [r['temps_sec'] for r in runners if r['genre'] == 'F']

    a_sorted = sorted(all_t)
    lo = int((quantile(a_sorted, 0.01) // BIN_SEC) * BIN_SEC)
    hi = int((quantile(a_sorted, 0.99) // BIN_SEC + 1) * BIN_SEC)

    g  = stats_from(all_t)
    gM = stats_from(men_t)
    gF = stats_from(wom_t)

    med = g['medianTime']
    print(f"  {len(runners)} finishers | médiane {med//3600}h{(med%3600)//60:02d}:{med%60:02d} | H:{len(men_t)} F:{len(wom_t)}")

    # Vérification : premier finisher
    if runners:
        t1 = runners[0]
        print(f"  OK 1er : #{t1['pos']} {t1['nom']} {t1['genre']} {t1['temps_str']}")

    output = {
        RACE_LABEL: {
            'global': g,
            'byGender': {'M': gM, 'F': gF},
            'finishHist': {
                'domain':      [lo, hi],
                'binSec':      BIN_SEC,
                'men':         make_hist(men_t, lo, hi),
                'women':       make_hist(wom_t, lo, hi),
                'menMedian':   gM.get('medianTime'),
                'womenMedian': gF.get('medianTime'),
            },
            'genderRankCurve': {
                'M': {'size': len(men_t), 'times': rank_curve(men_t)},
                'F': {'size': len(wom_t), 'times': rank_curve(wom_t)},
            },
            'runners': runners,
        }
    }

    out_path = 'stats.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))

    size_kb = __import__('os').path.getsize(out_path) // 1024
    print(f"OK stats.json sauvegarde ({size_kb} KB)")

if __name__ == '__main__':
    main()
