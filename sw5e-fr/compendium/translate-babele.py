#!/usr/bin/env python3
"""
Translate a Babele JSON file: read from translation-workbench, translate descriptions,
write to sw5e-fr/compendium. Preserves @UUID, [[/r ...]], HTML structure.
"""

import json, os, re, sys

SRC = r"C:\Users\QuentinGENSE\OneDrive - Airflux\Documents\Projet\Module_Traduction_ST5e\translation-workbench"
DST = r"C:\Users\QuentinGENSE\OneDrive - Airflux\Documents\Projet\Module_Traduction_ST5e\sw5e-fr\compendium"

# ── Pattern dictionaries ─────────────────────────────────────────────

TERMS = [
    ('temporary hit points', 'points de vie temporaires'),
    ('melee or ranged weapon attack', "attaque d'arme au corps à corps ou à distance"),
    ('ranged weapon attack', "attaque d'arme à distance"),
    ('melee weapon attack', "attaque d'arme au corps à corps"),
    ('melee or ranged weapon', 'arme de corps à corps ou à distance'),
    ('opportunity attack', "attaque d'opportunité"),
    ('weapon attack', "attaque d'arme"),
    ('melee attack', 'attaque au corps à corps'),
    ('ranged attack', 'attaque à distance'),
    ('bonus action', 'action bonus'),
    ('saving throw', 'jet de sauvegarde'),
    ('saving throws', 'jets de sauvegarde'),
    ('hit points', 'points de vie'),
    ('hit point', 'point de vie'),
    ('hit dice', 'dés de vie'),
    ('hit die', 'dé de vie'),
    ('proficiency bonus', 'bonus de maîtrise'),
    ('Armor Class', "Classe d'Armure"),
    ('armor class', "classe d'armure"),
    ('damage roll', 'jet de dégâts'),
    ('damage type', 'type de dégâts'),
    ('damage rolls', 'jets de dégâts'),
    ('ability check', 'test de caractéristique'),
    ('ability checks', 'tests de caractéristique'),
    ('ability score', 'score de caractéristique'),
    ('ability scores', 'scores de caractéristique'),
    ('ability modifier', 'modificateur de caractéristique'),
    ('Sleight of Hand', 'Escamotage'),
    ('Animal Handling', 'Dressage'),
    ('Force point', 'point de Force'),
    ('Force points', 'points de Force'),
    ('force point', 'point de Force'),
    ('force points', 'points de Force'),
    ('Force power', 'pouvoir de la Force'),
    ('Force powers', 'pouvoirs de la Force'),
    ('force power', 'pouvoir de la Force'),
    ('force powers', 'pouvoirs de la Force'),
    ('Tech point', 'point technique'),
    ('Tech power', 'pouvoir technique'),
    ('Tech powers', 'pouvoirs techniques'),
    ('tech power', 'pouvoir technique'),
    ('tech powers', 'pouvoirs techniques'),
    ('superiority die', 'dé de supériorité'),
    ('superiority dice', 'dés de supériorité'),
    ('proficiency die', 'dé de maîtrise'),
    ('proficiency dice', 'dés de maîtrise'),
    ('force die', 'dé de Force'),
    ('force dice', 'dés de Force'),
    ('short rest', 'repos court'),
    ('long rest', 'repos long'),
    ('movement speed', 'vitesse de déplacement'),
    ('unconscious', 'inconscient'),
    ('paralyzed', 'paralysé'),
    ('petrified', 'pétrifié'),
    ('poisoned', 'empoisonné'),
    ('restrained', 'entravé'),
    ('frightened', 'effrayé'),
    ('charmed', 'charmé'),
    ('deafened', 'assourdi'),
    ('blinded', 'aveuglé'),
    ('invisible', 'invisible'),
    ('stunned', 'étourdi'),
    ('grappled', 'agrippé'),
    ('prone', 'à terre'),
    ('exhaustion', 'épuisement'),
    ('Dexterity saving throw', 'jet de sauvegarde de Dextérité'),
    ('Strength saving throw', 'jet de sauvegarde de Force'),
    ('Constitution saving throw', 'jet de sauvegarde de Constitution'),
    ('Intelligence saving throw', "jet de sauvegarde d'Intelligence"),
    ('Wisdom saving throw', 'jet de sauvegarde de Sagesse'),
    ('Charisma saving throw', 'jet de sauvegarde de Charisme'),
    ('Strength check', 'test de Force'),
    ('Dexterity check', 'test de Dextérité'),
    ('Constitution check', 'test de Constitution'),
    ('Intelligence check', "test d'Intelligence"),
    ('Wisdom check', 'test de Sagesse'),
    ('Charisma check', 'test de Charisme'),
    ('advantage', 'avantage'),
    ('disadvantage', 'désavantage'),
    ('DC', 'DD'),
    ('damage', 'dégâts'),
    ('save', 'sauvegarde'),
    ('proficiency', 'maîtrise'),
    ('modifier', 'modificateur'),
    ('reaction', 'réaction'),
    ('feet', 'mètres'),
    ('self', 'personnelle'),
    ('touch', 'contact'),
    ('one creature', 'une créature'),
    ('one target', 'une cible'),
    ('15-foot cone', 'cône de 4,5 mètres'),
    ('15-foot radius', 'rayon de 4,5 mètres'),
    ('30-foot cone', 'cône de 9 mètres'),
    ('30-foot radius', 'rayon de 9 mètres'),
    ('60-foot cone', 'cône de 18 mètres'),
    ('60-foot radius', 'rayon de 18 mètres'),
    ('10-foot radius', 'rayon de 3 mètres'),
    ('20-foot radius', 'rayon de 6 mètres'),
    ('5-foot radius', 'rayon de 1,5 mètre'),
    ('5-foot square', 'case de 1,5 mètre'),
    ('10-foot square', 'case de 3 mètres'),
    ('15-foot square', 'case de 4,5 mètres'),
]

PHRASES = [
    ('Starting at', 'À partir du'),
    ('Beginning at', 'À partir du'),
    ('You can use your reaction to', 'Vous pouvez utiliser votre réaction pour'),
    ('You can use your action to', 'Vous pouvez utiliser votre action pour'),
    ('You can use a bonus action to', 'Vous pouvez utiliser une action bonus pour'),
    ('You can use an action to', 'Vous pouvez utiliser une action pour'),
    ('you can use a bonus action', 'vous pouvez utiliser une action bonus'),
    ('You can make', 'Vous pouvez faire'),
    ('You can add', 'Vous pouvez ajouter'),
    ('You can spend', 'Vous pouvez dépenser'),
    ('You can choose', 'Vous pouvez choisir'),
    ('you can choose', 'vous pouvez choisir'),
    ('You can increase', 'Vous pouvez augmenter'),
    ('You can reduce', 'Vous pouvez réduire'),
    ('You can deal', 'Vous pouvez infliger'),
    ('When you deal damage', 'Quand vous infligez des dégâts'),
    ('When you hit a creature', 'Quand vous touchez une créature'),
    ('When you hit with', 'Quand vous touchez avec'),
    ('When you use the Attack action', "Quand vous utilisez l'action Attaquer"),
    ('When you succeed', 'Quand vous réussissez'),
    ('when you succeed', 'quand vous réussissez'),
    ('When you fail', 'Quand vous échouez'),
    ('when you fail', 'quand vous échouez'),
    ('when you use', 'quand vous utilisez'),
    ('when you make', 'quand vous faites'),
    ('when you hit', 'quand vous touchez'),
    ('when you take damage', 'quand vous subissez des dégâts'),
    ('If you fail', 'Si vous échouez'),
    ('if you fail', 'si vous échouez'),
    ('If you succeed', 'Si vous réussissez'),
    ('if you succeed', 'si vous réussissez'),
    ('Once per turn', 'Une fois par tour'),
    ('once per turn', 'une fois par tour'),
    ('Once on each of your turns', 'Une fois par chacun de vos tours'),
    ('once on each of your turns', 'une fois par chacun de vos tours'),
    ('once per rest', 'une fois par repos'),
    ('On a failed save', "En cas d'échec"),
    ('On a successful save', 'En cas de réussite'),
    ('On a hit', 'En cas de toucher'),
    ('In addition', 'De plus'),
    ('Additionally', 'De plus'),
    ('a number of times equal to', 'un nombre de fois égal à'),
    ('You gain proficiency', 'Vous gagnez la maîtrise'),
    ('You gain a bonus', 'Vous gagnez un bonus'),
    ('You gain temporary hit points', 'Vous gagnez des points de vie temporaires'),
    ('You regain all', 'Vous regagnez tous'),
    ('of your choice', 'de votre choix'),
    ('each creature', 'chaque créature'),
    ('The target', 'La cible'),
    ('the target', 'la cible'),
    ('the creature', 'la créature'),
    ('that creature', 'cette créature'),
    ('that target', 'cette cible'),
    ('This feature', 'Cette aptitude'),
    ('This ability', 'Cette capacité'),
    ('This damage', 'Ces dégâts'),
    ('This effect', 'Cet effet'),
    ('until the end of your next turn', "jusqu'à la fin de votre prochain tour"),
    ('until the start of your next turn', "jusqu'au début de votre prochain tour"),
    ('until the end of your turn', "jusqu'à la fin de votre tour"),
    ('for 1 minute', 'pendant 1 minute'),
    ('You have advantage', "Vous avez l'avantage"),
    ('you have advantage', "vous avez l'avantage"),
    ('You have disadvantage', 'Vous avez le désavantage'),
    ('you have disadvantage', 'vous avez le désavantage'),
]

NAME_TERMS = [
    ('Ability Score Increase', "Augmentation de caractéristiques"),
    ('Ability Score', 'Score de caractéristique'),
    ('Saving Throw', 'Jet de sauvegarde'),
    ('Saving Throws', 'Jets de sauvegarde'),
    ('Armor Class', "Classe d'armure"),
    ('Natural Armor', 'Armure naturelle'),
    ('Fighting Style', 'Style de combat'),
    ('Bonus Proficiency', 'Maîtrise supplémentaire'),
    ('Bonus Proficiencies', 'Maîtrises supplémentaires'),
    ('Skill Proficiency', 'Compétence de maîtrise'),
]

# ── Translation functions ────────────────────────────────────────────

def needs_french(text):
    """Check if text already has French content (accents etc)."""
    return bool(re.search(r'[àâçéèêëîïôûùüÿœ]', text, re.IGNORECASE))

def has_english_content(text):
    """Check if text has significant English content that needs translation."""
    if not text or len(text.strip()) < 10:
        return False
    # If it already has French accents, assume translated
    if needs_french(text):
        return False
    # Check for English words
    en_words = [' the ', ' you ', ' your ', ' attack', ' damage', ' creature', 
                ' target', ' turn ', ' this ', ' hour', ' minute', ' round',
                ' when ', ' gain ', ' make ', ' deal ', ' hit ', ' save ',
                ' have ', ' can ', ' once ', ' each ', ' feet ', ' your ']
    text_lower = text.lower()
    return any(w in text_lower for w in en_words)

def translate_description(html):
    """Apply pattern-based translations to an HTML description."""
    if not html:
        return html
    if needs_french(html):
        return html  # Already translated
    if not has_english_content(html):
        return html
    
    # Level headers
    html = re.sub(r'(\d+)(?:st|nd|rd|th)\s+and\s+(\d+)(?:st|nd|rd|th)\s+level', r'niveaux \1 et \2', html)
    html = re.sub(r'(\d+)(?:st|nd|rd|th)\s+level', r'niveau \1', html)
    html = html.replace('13th level, 17th level, and 20th level', 'niveaux 13, 17 et 20')
    html = html.replace('level', 'niveau')
    html = html.replace('Level', 'Niveau')
    
    # Game terms
    for old, new in TERMS:
        html = html.replace(old, new)
    
    # Phrases
    for old, new in PHRASES:
        html = html.replace(old, new)
    
    return html

def translate_name(name):
    """Translate a name using term substitution."""
    if not name:
        return name
    if needs_french(name):
        return name
    result = name
    for old, new in NAME_TERMS:
        result = result.replace(old, new)
    return result

# ── Main ─────────────────────────────────────────────────────────────

def translate_file(filename):
    """Read a file from SRC, translate, write to DST."""
    src_path = os.path.join(SRC, filename)
    dst_path = os.path.join(DST, filename)
    
    if not os.path.exists(src_path):
        print(f"  NOT FOUND: {filename}")
        return
    
    with open(src_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    
    entries = data.get('entries', {})
    total = len(entries)
    translated = 0
    name_translated = 0
    
    for key, entry in entries.items():
        old_name = entry.get('name', '')
        old_desc = entry.get('description', '') or ''
        
        new_name = translate_name(old_name)
        new_desc = translate_description(old_desc)
        
        if new_name != old_name:
            entry['name'] = new_name
            name_translated += 1
        if new_desc != old_desc:
            entry['description'] = new_desc
            translated += 1
    
    with open(dst_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"  {filename}: {total} entries, {name_translated} names + {translated} descriptions translated")

if __name__ == '__main__':
    files = sys.argv[1:]
    if not files:
        print("Usage: python translate-babele.py <file1.json> [file2.json ...]")
        sys.exit(1)
    
    for fn in files:
        translate_file(fn)
