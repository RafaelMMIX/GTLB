# Grand Theft Lamotte-Beuvron

Parodie de GTA en 2D vue du dessus, jouable dans le navigateur, qui se déroule dans la vraie ville de Lamotte-Beuvron (Loir-et-Cher) à partir du plan OpenStreetMap.

## Jouer

Ouvre `index.html` via un petit serveur (le jeu charge `data.json`) :

    python3 -m http.server 8000

puis va sur http://localhost:8000. Ou active GitHub Pages sur ce dépôt.

## Commandes

- ZQSD / flèches : marcher, conduire · Maj : courir · Espace : frein à main
- E : monter/descendre, entrer dans un lieu · H : klaxon
- V : appeler ta voiture · R : radio · T : téléphone · Tab / C : grande carte · M : son

## Contenu

Missions de Mme Tatin, police (barrages, hélicoptère), garage et boutique, commerces, trains avec barrières, sangliers, chevaux, téléphone (Lamotte-Gram, GPS, taxi, banque, succès).

## Refaire une autre carte

Exporte une zone depuis openstreetmap.org, puis `python3 tools/build_data.py map.osm data.json` pour régénérer `data.json`.

## Crédits

Données cartographiques © les contributeurs d'OpenStreetMap, licence ODbL : https://www.openstreetmap.org/copyright

## Cartes

- **Lamotte-Beuvron** (par défaut) : `index.html`
- **Romorantin-Lanthenay** (à pied uniquement, accessible en train depuis la gare de Lamotte) : `index.html?map=romo`

Les fichiers `data.json`, `data_romo.json` et `logo.png` doivent rester dans le même dossier que `index.html`.
Les données de carte sont générées avec `tools/build_data.py SRC.osm OUT.json [poi.json]`.

Carte : © les contributeurs d'OpenStreetMap (ODbL)
