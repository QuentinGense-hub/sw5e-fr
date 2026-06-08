#!/usr/bin/env python3
"""
MT translate remaining English text in Babele JSON files.
One text at a time for reliability. Respects rate limits.
"""

import json, os, re, sys, time, requests, concurrent.futures

SRC = r'C:\Users\QuentinGENSE\OneDrive - Airflux\Documents\Projet\Module_Traduction_ST5e\sw5e-fr\compendium'

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
TL_URL = 'https://translate.googleapis.com/translate_a/single'

def translate_one(text, retries=3):
    """Translate a single text string."""
    if not text or len(text.strip()) < 3:
        return text
    
    params = {'client': 'gtx', 'sl': 'en', 'tl': 'fr', 'dt': 't', 'q': text}
    
    for attempt in range(retries):
        try:
            resp = requests.get(TL_URL, params=params, timeout=30, headers={'User-Agent': UA})
            if resp.status_code == 200:
                parts = []
                for sentence in resp.json()[0]:
                    if sentence[0]:
                        parts.append(sentence[0])
                return ''.join(parts)
            elif resp.status_code == 429:
                time.sleep(3 ** attempt)
            else:
                time.sleep(1)
        except:
            time.sleep(2)
    return text


def is_french(text):
    return bool(re.search(r'[àâçéèêëîïôûùüÿœ]', text, re.IGNORECASE))


def has_english(text):
    if not text or len(text.strip()) < 4:
        return False
    if is_french(text):
        return False
    return bool(re.search(r'\b(the|you|your|and|for|this|that|with|from|when|can|gain|have|deal|make|hit|save|once|each|every|turn|attack|damage|creature|target|bonus|action|reaction|feature|ability|level|check|throw|point|power|minute|hour|round|your|their|they|them|roll|foot|feet|range|weapon|armor|class|until|during|before|after|while|within|without|other|another|number|equal|twice|times|choose|spend|increase|reduce|instead|unless|whether|both|each|more|less|than|then|also|must|may|cannot)\b', text, re.IGNORECASE))


def protect_and_translate(html_text):
    """Translate HTML while preserving tags and Foundry markup."""
    protected = {}
    idx = [0]
    
    def stash(m):
        ph = f'ZZPH{idx[0]:04d}PHZZ'
        protected[ph] = m.group(0)
        idx[0] += 1
        return ph
    
    text = html_text
    
    # Protect Foundry special tags (order matters: more specific first)
    for pat in [
        r'@UUID\[[^\]]*\]',
        r'@Compendium\[[^\]]*\]',
        r'@(?:Ability|Skill|Condition|Item|Actor|JournalEntry|RollTable)\[[^\]]*\]',
        r'\[\[/r\s*[^\]]*\]\]',
        r'\[\[/save[^\]]*\]\]',
        r'\[\[/damage[^\]]*\]\]',
        r'\[\[/[a-z]+\s*[^\]]*\]\]',
        r'<a[^>]*href="[^"]*"[^>]*>',
        r'</a>',
        r'<[^>]*>',
    ]:
        text = re.sub(pat, stash, text)
    
    # Normalize whitespace for better translation
    text = re.sub(r'\s+', ' ', text).strip()
    
    if not has_english(text):
        return html_text
    
    translated = translate_one(text)
    
    if not translated or translated == text:
        return html_text
    
    # Restore protected items
    for ph, orig in sorted(protected.items(), key=lambda x: -len(x[0])):
        translated = translated.replace(ph, orig)
    
    # Handle HTML entities Google might have mangled (avoid double-escaping)
    for old, new in [('&amp;', '&'), ('&amp;amp;', '&'), ('&lt;', '<'), ('&gt;', '>'),
                     ('&quot;', '"'), ('&#39;', "'")]:
        translated = translated.replace(old, new)
    
    return translated


def translate_file(filename):
    path = os.path.join(SRC, filename)
    if not os.path.exists(path):
        print(f'  NOT FOUND: {filename}')
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entries = data.get('entries', {})
    
    # Phase 1: pattern-based
    for entry in entries.values():
        desc = entry.get('description', '') or ''
        name = entry.get('name', '') or ''
        
        for old, new in TERMS:
            desc = desc.replace(old, new)
            name = name.replace(old, new)
        for old, new in PHRASES:
            desc = desc.replace(old, new)
        for old, new in NAME_TERMS:
            name = name.replace(old, new)
        
        entry['description'] = desc
        entry['name'] = name
    
    # Phase 2: collect texts needing MT
    todo = []
    for key, entry in entries.items():
        name = entry.get('name', '') or ''
        desc = entry.get('description', '') or ''
        if name and not is_french(name) and has_english(name):
            todo.append((key, 'name'))
        if desc and not is_french(desc) and has_english(desc):
            todo.append((key, 'description'))
    
    if not todo:
        print(f'  {filename}: already fully translated')
        return
    
    print(f'  {filename}: {len(todo)} texts to translate via API')
    
    for i, (key, field) in enumerate(todo):
        text = entries[key][field]
        translated = protect_and_translate(text)
        if translated and translated != text:
            entries[key][field] = translated
        
        if (i + 1) % 10 == 0:
            print(f'    {i+1}/{len(todo)}')
        
        time.sleep(0.3)  # Rate limit
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f'  {filename}: done ({len(todo)} texts)')


# ── Patterns ────────────────────────────────────────────────────────

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
    ('You gain resistance', 'Vous gagnez la résistance'),
    ('You gain a bonus', 'Vous gagnez un bonus'),
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
    ('You gain temporary hit points', 'Vous gagnez des points de vie temporaires'),
    ('You learn one additional', 'Vous apprenez un supplémentaire'),
    ('You learn an additional', 'Vous apprenez un supplémentaire'),
]

NAME_TERMS = [
    ('Ability Score Increase', 'Augmentation de caractéristiques'),
    ('Ability Score', 'Score de caractéristique'),
    ('Saving Throw', 'Jet de sauvegarde'),
    ('Saving Throws', 'Jets de sauvegarde'),
    ('Armor Class', "Classe d'armure"),
    ('Natural Armor', 'Armure naturelle'),
    ('Fighting Style', 'Style de combat'),
    ('Bonus Proficiency', 'Maîtrise supplémentaire'),
    ('Bonus Proficiencies', 'Maîtrises supplémentaires'),
    ('Skill Proficiency', 'Compétence de maîtrise'),
    ('Tool Proficiency', "Maîtrise d'outil"),
    ('Weapon Proficiency', "Maîtrise d'arme"),
    ('Armor Proficiency', "Maîtrise d'armure"),
    ('Unarmored Defense', 'Défense sans armure'),
]


if __name__ == '__main__':
    files = sys.argv[1:] if len(sys.argv) > 1 else None
    
    if files:
        for fn in files:
            translate_file(fn)
    else:
        all_files = sorted([f for f in os.listdir(SRC) if f.endswith('.json')
                          and not f.startswith('translate') and f != 'classfeatures-names.json'])
        for fn in all_files:
            translate_file(fn)
