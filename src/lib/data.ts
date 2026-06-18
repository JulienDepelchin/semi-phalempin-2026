import { base } from '$app/paths';

export type Race = '10km' | '6km';

export interface Runner {
	dossard: string;
	nom: string;
	annee: string;
	club: string;
	temps_str: string;
	temps_sec: number;
	genre: 'M' | 'F';
	pos: number;
}

export interface GenderCurve {
	size: number;
	times: number[];
}

export interface FinishHist {
	domain: [number, number];
	binSec: number;
	men: number[];
	women: number[];
	menMedian: number;
	womenMedian: number;
}

export interface RaceStats {
	global: { n: number; medianTime: number; p10: number; p25: number; p75: number; p90: number; fastest: number; slowest: number };
	byGender: { M: { n: number; medianTime: number }; F: { n: number; medianTime: number } };
	finishHist: FinishHist;
	genderRankCurve: { M: GenderCurve; F: GenderCurve };
	runners: Runner[];
}

export type StatsJson = Record<Race, RaceStats>;

let cache: StatsJson | null = null;

export async function loadStats(): Promise<StatsJson> {
	if (cache) return cache;
	const res = await fetch(`${base}/stats.json`);
	if (!res.ok) throw new Error(`Failed to load stats.json: ${res.status}`);
	cache = await res.json();
	return cache!;
}

/** "DUPONT, Jean" → "Jean DUPONT" */
export function formatName(nom: string): string {
	const comma = nom.indexOf(',');
	if (comma === -1) return nom;
	const last = nom.slice(0, comma).trim();
	const first = nom.slice(comma + 1).trim();
	return first ? `${first} ${last}` : last;
}

export function search(runners: Runner[], query: string): Runner[] {
	const q = query.trim().toLowerCase();
	if (!q) return [];
	const byDossard = runners.filter((r) => r.dossard === q);
	if (byDossard.length > 0) return byDossard;
	return runners
		.filter((r) => r.nom.toLowerCase().includes(q) || formatName(r.nom).toLowerCase().includes(q))
		.slice(0, 20);
}

export function fmtTime(sec: number): string {
	const h = Math.floor(sec / 3600);
	const m = Math.floor((sec % 3600) / 60);
	const s = sec % 60;
	if (h > 0) return `${h}h${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
	return `${m}:${String(s).padStart(2, '0')}`;
}

export function fmtPace(sec: number, distKm: number): string {
	const paceS = sec / distKm;
	const m = Math.floor(paceS / 60);
	const s = Math.round(paceS % 60);
	return `${m}'${String(s).padStart(2, '0')}"`;
}

export function fmtThousands(n: number): string {
	return Math.round(n).toLocaleString('fr-FR');
}

export function genderRank(curve: GenderCurve, timeSec: number): number {
	const { times, size } = curve;
	let lo = 0, hi = times.length - 1;
	while (lo < hi) {
		const mid = (lo + hi) >> 1;
		if (times[mid] < timeSec) lo = mid + 1;
		else hi = mid;
	}
	return Math.round((lo / times.length) * size) + 1;
}

export function fasterThanPct(pos: number, total: number): number {
	return Math.round(((total - pos) / total) * 100);
}

/** FFA categories by birth year */
export function getCategory(annee: string, genre: 'M' | 'F'): string {
	const b = parseInt(annee);
	if (!b || isNaN(b)) return genre === 'F' ? 'FSE' : 'SE';
	const f = genre === 'F';
	if (b >= 2020) return f ? 'FBB' : 'BB';
	if (b >= 2017) return f ? 'FEA' : 'EA';
	if (b >= 2015) return f ? 'FPO' : 'PO';
	if (b >= 2013) return f ? 'FBE' : 'BE';
	if (b >= 2011) return f ? 'FMI' : 'MI';
	if (b >= 2009) return f ? 'FCA' : 'CA';
	if (b >= 2007) return f ? 'FJU' : 'JU';
	if (b >= 2004) return f ? 'FES' : 'ES';
	if (b >= 1992) return f ? 'FSE' : 'SE';
	if (b >= 1987) return f ? 'F0'  : 'M0';
	if (b >= 1982) return f ? 'F1'  : 'M1';
	if (b >= 1977) return f ? 'F2'  : 'M2';
	if (b >= 1972) return f ? 'F3'  : 'M3';
	if (b >= 1967) return f ? 'F4'  : 'M4';
	if (b >= 1962) return f ? 'F5'  : 'M5';
	if (b >= 1957) return f ? 'F6'  : 'M6';
	if (b >= 1952) return f ? 'F7'  : 'M7';
	if (b >= 1947) return f ? 'F8'  : 'M8';
	if (b >= 1942) return f ? 'F9'  : 'M9';
	return f ? 'F10' : 'M10';
}

const CAT_LABELS: Record<string, string> = {
	BB:'Baby', FBB:'Baby Femme',
	EA:'Éveil Athlétisme', FEA:'Éveil Athlétisme Femme',
	PO:'Poussin', FPO:'Poussine',
	BE:'Benjamin', FBE:'Benjamine',
	MI:'Minime', FMI:'Minime Femme',
	CA:'Cadet', FCA:'Cadette',
	JU:'Junior Homme', FJU:'Junior Femme',
	ES:'Espoir Homme', FES:'Espoir Femme',
	SE:'Senior Homme', FSE:'Senior Femme',
	M0:'Master 0 Homme', F0:'Master 0 Femme',
	M1:'Master 1 Homme', F1:'Master 1 Femme',
	M2:'Master 2 Homme', F2:'Master 2 Femme',
	M3:'Master 3 Homme', F3:'Master 3 Femme',
	M4:'Master 4 Homme', F4:'Master 4 Femme',
	M5:'Master 5 Homme', F5:'Master 5 Femme',
	M6:'Master 6 Homme', F6:'Master 6 Femme',
	M7:'Master 7 Homme', F7:'Master 7 Femme',
	M8:'Master 8 Homme', F8:'Master 8 Femme',
	M9:'Master 9 Homme', F9:'Master 9 Femme',
	M10:'Master 10 Homme', F10:'Master 10 Femme',
};

export function getCategoryLabel(cat: string): string {
	return CAT_LABELS[cat] ?? cat;
}

export function marathonEquiv(sec: number, distKm: number): number {
	return Math.round((sec / distKm) * 42.195);
}

export function linScale(
	domain: [number, number],
	range: [number, number]
): (v: number) => number {
	const [d0, d1] = domain;
	const [r0, r1] = range;
	return (v) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);
}

/** Seeded PRNG (LCG) for reproducible random positions */
export function seededRng(seed: number): () => number {
	let s = (Math.abs(seed) * 7 + 13) >>> 0;
	return () => {
		s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
		return s / 4294967295;
	};
}

/** Logical category sort order (youngest → oldest) */
export const CAT_ORDER = [
	'BB','FBB','EA','FEA','PO','FPO','BE','FBE','MI','FMI',
	'CA','FCA','JU','FJU','ES','FES','SE','FSE',
	'M0','F0','M1','F1','M2','F2','M3','F3','M4','F4',
	'M5','F5','M6','F6','M7','F7','M8','F8','M9','F9','M10','F10',
];
