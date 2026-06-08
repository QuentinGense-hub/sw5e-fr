#!/usr/bin/env python3
"""
AGGRESSIVE final pass: translate EVERY name and description that still has English.
Uses a conservative check: English words OR no accents AND looks like English.
But translates ALL names that don't have French accents (using a skip list for known FR terms).
"""

import json, os, re, sys, time, requests

SRC = r'C:\Users\QuentinGENSE\OneDrive - Airflux\Documents\Projet\Module_Traduction_ST5e\sw5e-fr\compendium'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
TL_URL = 'https://translate.googleapis.com/translate_a/single'

ac = re.compile(r'[àâçéèêëîïôûùüÿœ]', re.I)
en_word = re.compile(r'\b(the|you|your|and|for|this|that|with|from|when|can|gain|have|deal|hit|save|once|each|every|turn|attack|damage|creature|target|bonus|action|reaction|feature|ability|level|check|throw|point|power|minute|hour|round|feet|range|weapon|armor|class|until|during|before|after|while|within|without|other|another|number|equal|twice|times|choose|spend|increase|reduce|instead|unless|whether|both|each|more|less|than|then|also|must|may|proficient|survival|stealth|perception|insight|acrobatics|athletics|investigation|sleight|handling|initiative)\b', re.I)

# Known French game terms without accents (to avoid re-translating them)
FR_TERMS = {
    'force', 'sagesse', 'charisme', 'intelligence', 'constitution', 'dexterite',
    'action bonus', 'repos court', 'repos long',
    'points de vie', 'des de vie', 'de de vie', 'jet de sauvegarde',
    'jets de sauvegarde', 'classe d armure', 'bonus de maitrise',
    'modificateur', 'dexterite', 'maitrise', 'reaction',
    'de degats', 'type de degats', 'de maitrise',
    'de superiority', 'de force', 'test de force',
    'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma',
    'strength', 'dexterite',  # sometimes partially translated
}

def is_french_word(word):
    return word.lower() in FR_TERMS

def has_french_terms(text):
    """Check if the text contains known French game terms."""
    words = re.findall(r'[a-zàâçéèêëîïôûùüÿœ-]+', text.lower())
    fr_count = sum(1 for w in words if w in FR_TERMS)
    return fr_count >= len(words) * 0.3  # 30% of words are French terms

def needs_translation(text, field_type='description'):
    """Determine if text needs MT translation."""
    if not text or len(text.strip()) < 2:
        return False
    if ac.search(text):
        return False  # Has French accents - already translated
    
    text_clean = text.strip()
    
    if field_type == 'name':
        # Names: translate if it has English words OR no known French terms
        if has_french_terms(text_clean):
            return False
        if en_word.search(text_clean):
            return True
        # Short names without obvious English or French - still translate
        # (things like "Insurgent", "Ace Pilot", etc.)
        if len(text_clean) > 3 and any(c.isalpha() for c in text_clean):
            return True
        return False
    else:
        # Descriptions: must have English words to need translation
        return bool(en_word.search(text_clean))


def translate_one(text, retries=3):
    if not text or len(text.strip()) < 2:
        return text
    params = {'client': 'gtx', 'sl': 'en', 'tl': 'fr', 'dt': 't', 'q': text}
    for attempt in range(retries):
        try:
            resp = requests.get(TL_URL, params=params, timeout=30, headers={'User-Agent': UA})
            if resp.status_code == 200:
                parts = [s[0] for s in resp.json()[0] if s[0]]
                return ''.join(parts)
            elif resp.status_code == 429:
                time.sleep(3 ** attempt)
            else:
                time.sleep(0.5)
        except:
            time.sleep(1)
    return text


total = 0
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith('.json') or fn.startswith('translate') or fn == 'classfeatures-names.json':
        continue
    
    path = os.path.join(SRC, fn)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entries = data.get('entries', {})
    todo = []
    
    for key, entry in entries.items():
        name = (entry.get('name', '') or '').strip()
        desc = (entry.get('description', '') or '').strip()
        if name and needs_translation(name, 'name'):
            todo.append((key, 'name'))
        if desc and needs_translation(desc, 'description'):
            todo.append((key, 'description'))
    
    if not todo:
        print(f'{fn}: OK')
        continue
    
    print(f'{fn}: {len(todo)} to translate')
    for i, (key, field) in enumerate(todo):
        text = entries[key][field]
        translated = translate_one(text)
        if translated and translated != text and len(translated) > 0:
            entries[key][field] = translated
        total += 1
        if (i+1) % 10 == 0:
            print(f'  {i+1}/{len(todo)}')
        time.sleep(0.2)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

print(f'\nDone! {total} texts translated')
