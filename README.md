# SW5E - Traduction Française

Module de traduction française pour le module Foundry VTT [SW5E](https://github.com/sw5e-foundry/sw5e-module).

## Fonctionnalités

- Traduction française des libellés principaux du module SW5E.
- Traduction des états SW5E : Corrodé, Enflammé, Électrisé, Ralenti, Affaibli.
- Traduction Babele du compendium `sw5e.conditions`, avec noms et descriptions des états.
- Traduction Babele des compendiums `sw5e.armorproperties` et `sw5e.weaponproperties`.
- Outil d'export des templates Babele pour traduire progressivement les autres compendiums SW5E.

## Packs traduits

- `sw5e.adventuringgear`
- `sw5e.ammo`
- `sw5e.archetypefeatures`
- `sw5e.archetypes`
- `sw5e.armor`
- `sw5e.armorproperties`
- `sw5e.backgrounds`
- `sw5e.blasters`
- `sw5e.classes`
- `sw5e.classfeatures`
- `sw5e.conditions`
- `sw5e.consumables`
- `sw5e.deploymentfeatures`
- `sw5e.deployments`
- `sw5e.drakes-shipyard`
- `sw5e.enhanceditems`
- `sw5e.explosives`
- `sw5e.feats`
- `sw5e.fightingmasteries`
- `sw5e.fightingstyles`
- `sw5e.fistoscodex`
- `sw5e.forcepowers`
- `sw5e.gamingsets`
- `sw5e.implements`
- `sw5e.invocations`
- `sw5e.kits`
- `sw5e.lightsaberforms`
- `sw5e.lightweapons`
- `sw5e.maneuvers`
- `sw5e.modifications`
- `sw5e.monster_temp`
- `sw5e.monsters`
- `sw5e.monstertraits`
- `sw5e.musicalinstruments`
- `sw5e.species`
- `sw5e.speciesfeatures`
- `sw5e.starshipactions`
- `sw5e.starshiparmor`
- `sw5e.starshipequipment`
- `sw5e.starshipfeatures`
- `sw5e.starshipmodifications`
- `sw5e.starships`
- `sw5e.starshipweapons`
- `sw5e.tables`
- `sw5e.techpowers`
- `sw5e.ventures`
- `sw5e.vibroweapons`
- `sw5e.weaponproperties`

## Installation locale

1. Copiez le dossier `sw5e-fr` dans `{FoundryData}/Data/modules/sw5e-fr`.
2. Installez et activez le module SW5E.
3. Installez et activez le module Babele.
4. Activez `SW5E - Traduction Française` dans votre monde DnD5e.
5. Passez la langue de Foundry en français.

## Traduire les autres compendiums

Le dépôt SW5E contient près de 9 000 documents de compendium. Pour éviter de casser les liens et UUID Foundry, les traductions de contenu doivent passer par Babele.

Depuis le dossier parent qui contient `sw5e-fr` et `upstream-sw5e-module`, lancez :

```powershell
node .\sw5e-fr\tools\export-babele-templates.mjs --source .\upstream-sw5e-module --out .\sw5e-fr\translation-workbench
```

Traduisez ensuite les fichiers JSON générés dans `translation-workbench`. Quand un pack est prêt, déplacez le fichier correspondant dans `sw5e-fr/compendium`. Exemple : `sw5e.forcepowers.json`.

Pour générer uniquement certains packs :

```powershell
node .\sw5e-fr\tools\export-babele-templates.mjs --source .\upstream-sw5e-module --out .\sw5e-fr\translation-workbench --only conditions,classes,forcepowers,techpowers
```

## Notes

- Les clés de traduction d'interface sont dans `lang/fr.json`.
- Les traductions de compendiums chargées par Babele sont dans `compendium/`.
- Les fichiers de travail générés dans `translation-workbench/` ne sont pas chargés par Foundry tant qu'ils ne sont pas déplacés dans `compendium/`.
