# Course des 2 Stades Domitys 2026

App SvelteKit de résultats personnalisés — 7 slides animées, scroll-snap, palette sombre.

## Setup

```bash
npm install

# Obligatoire pour GitHub Pages : empêche Jekyll d'ignorer le dossier _app/
touch static/.nojekyll
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

> **Note** : `static/.nojekyll` doit être présent avant le build.  
> Sans ce fichier, GitHub Pages (mode legacy) ignore `_app/` et sert une page blanche.

## Régénérer stats.json

```bash
python scripts/build_stats.py
cp stats.json static/stats.json
npm run build && npm run deploy
```
