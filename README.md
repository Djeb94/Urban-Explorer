# Urban Data Explorer

Exploration de données urbaines parisiennes : prix immobiliers, criminalité, espaces verts, transports, logements sociaux et mixité sociale, agrégés par arrondissement et restitués sous forme de carte interactive et d'indicateurs synthétiques.

## Sommaire

- [Architecture](#architecture)
- [Choix de stack](#choix-de-stack)
- [Lancer le projet](#lancer-le-projet)

## Architecture

Le projet est découpé en trois grands blocs :

```
data/        Données brutes, nettoyées et indicateurs calculés (Bronze / Silver / Gold)
scripts/     Pipeline d'ingestion et de calcul des indicateurs
api/         API FastAPI qui sert les données au frontend
frontend/    Application React de visualisation (carte + graphiques)
```

### Pipeline de données : architecture en médaillon (Bronze / Silver / Gold)

Les données proviennent de sources publiques hétérogènes (data.gouv.fr, Paris Open Data, INSEE, IDF Mobilités, OpenStreetMap, data.culture.gouv.fr). Pour gérer cette hétérogénéité sans tout recalculer à chaque requête, le pipeline suit trois étapes :

- **Bronze** (`data/bronze/`) : données brutes telles que téléchargées (CSV, GeoJSON, shapefiles), conservées sans transformation pour pouvoir rejouer le pipeline si une règle de nettoyage change.
- **Silver** (`data/silver/`) : données nettoyées, filtrées sur Paris et agrégées par arrondissement (un fichier par thématique : transactions, revenus, criminalité, logements sociaux, espaces verts, stations, vivacité urbaine).
- **Gold** (`data/gold/`) : quatre indicateurs composites calculés à partir des tables Silver (accessibilité à l'achat, vivabilité urbaine, attractivité, mixité sociale), prêts à être consommés par l'API.

Ce découpage permet de séparer la collecte (lente, dépendante de sources externes), le nettoyage (logique métier par source) et le calcul d'indicateurs (logique d'agrégation transverse), et d'isoler les pannes d'une source sans bloquer les autres.

### Stockage : PostgreSQL + MongoDB

Deux bases sont utilisées en fonction de la nature des données :

- **PostgreSQL** (hébergé sur Supabase) pour les données tabulaires et temporelles : transactions immobilières, revenus, criminalité, indicateurs Gold. Ces données sont relationnelles par nature (jointures par arrondissement et par année) et bénéficient d'un moteur SQL classique.
- **MongoDB** (hébergé sur MongoDB Atlas) pour les données géospatiales restituées en GeoJSON : contours d'arrondissements, logements sociaux, espaces verts, stations. Le stockage document colle directement au format consommé par la carte (`FeatureCollection`), sans étape de sérialisation côté API.

### API : FastAPI

L'API expose les indicateurs et les couches géographiques via des routes REST simples (`/ind1` à `/ind4`, `/transactions`, `/contours`, `/timeline`, etc.), avec documentation interactive générée automatiquement (Swagger). Un job planifié (APScheduler) recalcule périodiquement l'indicateur d'accessibilité à partir des données Silver, pour refléter l'évolution des prix sans intervention manuelle.

### Frontend : React + MapLibre

- **React** pour la gestion de l'état de l'interface (indicateur sélectionné, arrondissement survolé, mode comparaison).
- **MapLibre GL / react-map-gl** pour le rendu de carte vectorielle : solution open-source, sans clé API ni coût d'usage, suffisante pour une carte choroplèthe par arrondissement.
- **Recharts** pour les graphiques d'évolution temporelle des prix.
- **Vite** comme outil de build, pour un démarrage et un rechargement à chaud rapides en développement.

## Choix de stack

| Composant | Choix | Justification |
|---|---|---|
| Backend | Python / FastAPI | Le pipeline de données (pandas, geopandas) est déjà en Python ; FastAPI permet de réutiliser le même langage pour l'API sans changement de contexte, avec une documentation auto-générée. |
| Frontend | React + Vite | Écosystème mature pour les interfaces orientées données, large choix de librairies de cartographie et de graphiques. |
| Cartographie | MapLibre GL | Fork open-source de Mapbox GL, sans dépendance à une clé API payante, suffisant pour des couches choroplèthes et des popups. |
| Base relationnelle | PostgreSQL (Supabase) | Données tabulaires avec relations naturelles (arrondissement, année) ; hébergement managé gratuit en développement. |
| Base documentaire | MongoDB (Atlas) | Données déjà au format GeoJSON en sortie de pipeline ; évite une couche de transformation SQL → GeoJSON côté API. |
| Orchestration des recalculs | APScheduler | Recalcul périodique simple (hebdomadaire) sans avoir à introduire un orchestrateur externe pour un seul job. |

## Lancer le projet

Terminal 1 :

    cd Urban-Explorer
    uvicorn api.main:app --reload

Terminal 2 : 

    cd frontend
    nvm use 20 (depend de la version)
    npm run dev