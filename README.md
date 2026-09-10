# Semi-Marathon de Phalempin 2026 — résultats personnalisés

Application SvelteKit qui affiche, à partir d'un numéro de dossard, un récapitulatif
animé de sept écrans : temps, allure, rang, position dans le peloton, catégorie
d'âge, puis une image de partage pour les réseaux sociaux.

Le principe est celui d'un « Wrapped » de fin d'année appliqué à une course locale.

## Nature technique

- **100 % statique.** Le build produit un dossier de fichiers HTML, CSS, JS et un
  fichier de données. Aucun serveur applicatif, aucune base de données, aucune API.
- **Aucun appel réseau côté serveur.** Le dossard saisi ne quitte pas le navigateur ;
  tous les calculs et le rendu de l'image de partage sont faits côté client.
- **Données.** `static/stats.json` est généré une fois à partir du classement
  officiel (public) de l'épreuve. Il contient nom, année de naissance et club de
  chaque finisher — les mêmes informations que le classement diffusé par
  l'organisateur.
- **Mesure d'audience.** Umami, sans cookie ni identifiant persistant (pas de
  bandeau de consentement). Trois événements anonymes : `recherche_dossard`,
  `story_generee`, `partage`.
- **Ressources externes chargées par le navigateur du visiteur :** polices Google
  Fonts, script Umami, liens de partage (X, Facebook, WhatsApp). Les deux premières
  sont internalisables.

## Setup

```bash
npm install

# Obligatoire pour GitHub Pages : empêche Jekyll d'ignorer le dossier _app/
# (déjà présent dans le repo : static/.nojekyll)
```

## Développement

```bash
npm run dev
```

## Build & déploiement

```bash
npm run build        # → build/
npm run deploy       # pousse build/ sur la branche gh-pages
```

> `static/.nojekyll` doit être présent avant le build. Sans ce fichier, GitHub Pages
> (mode legacy) ignore `_app/` et sert une page blanche.

Le chemin de base est configurable :

```bash
BASE_PATH=/mon-chemin npm run build
```

## Régénérer les statistiques

```bash
python scripts/build_stats.py <classement.pdf>   # → stats.json (racine, ignoré par git)
cp stats.json static/stats.json
npm run build && npm run deploy
```

`scripts/build_stats.py` attend le format PDF du chronométreur de Phalempin
(regex `LINE_RE`). Un autre prestataire de chronométrage = une autre mise en page =
une adaptation de l'extraction.

## Décliner pour une autre course

Le cœur de l'application est réutilisable tel quel. À adapter :

| Élément | Où |
| --- | --- |
| Distance (`21km` / `21.1`) | `src/routes/+page.svelte`, `src/lib/data.ts` |
| Nom et année de l'épreuve | `src/app.html`, `CoverSlide.svelte`, `PartageSlide.svelte` |
| Calcul des tranches d'âge (année de référence) | `CourseDansLaCourseSlide.svelte`, `scripts/build_stats.py` (`CAT_YEAR`) |
| `og:url` / `og:image` | `src/app.html` |
| Chemin de base | variable `BASE_PATH` (voir ci-dessus) |
| Identifiant Umami | `src/app.html` (`data-website-id`) |
| Parsing du classement | `scripts/build_stats.py` |

## Historique

Fork de « Course des 2 Stades Domitys », adapté au Semi-Marathon de Phalempin.
