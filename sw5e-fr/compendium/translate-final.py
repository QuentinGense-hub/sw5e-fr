#!/usr/bin/env python3
"""Final pass: translate ANY description without French accents."""
import json, os, re, sys, time, requests

SRC = r'C:\Users\QuentinGENSE\OneDrive - Airflux\Documents\Projet\Module_Traduction_ST5e\sw5e-fr\compendium'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
TL_URL = 'https://translate.googleapis.com/translate_a/single'

def translate_one(text, retries=3):
    if not text or len(text.strip()) < 3:
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
                time.sleep(1)
        except:
            time.sleep(2)
    return text

ac = re.compile(r'[àâçéèêëîïôûùüÿœ]', re.I)
en_check = re.compile(r'\b(the|you|your|and|for|this|that|with|from|can|gain|have|deal|hit|once|each|every|turn|attack|damage|creature|target|bonus|action|reaction|feature|ability|level|check|throw|point|power|minute|hour|round|feet|range|weapon|armor|class|until|during|before|after|while|within|without|other|another|number|equal|twice|times|choose|spend|increase|reduce|instead|unless|whether|both|each|more|less|than|then|also|must|may|proficient|survival|stealth|perception|insight|acrobatics|athletics|investigation)\b', re.I)

def needs_translation(text):
    if not text or len(text.strip()) < 4:
        return False
    if ac.search(text):
        return False
    if en_check.search(text.lower()):
        return True
    return False

for fn in sorted(os.listdir(SRC)):
    if not fn.endswith('.json') or fn.startswith('translate') or fn == 'classfeatures-names.json':
        continue
    
    path = os.path.join(SRC, fn)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entries = data.get('entries', {})
    todo = []
    
    for key, entry in entries.items():
        desc = (entry.get('description', '') or '')
        if needs_translation(desc):
            todo.append((key, 'description'))
    
    if not todo:
        continue
    
    print(f'{fn}: {len(todo)} remaining')
    for i, (key, field) in enumerate(todo):
        text = entries[key][field]
        translated = translate_one(text)
        if translated and translated != text:
            entries[key][field] = translated
        if (i+1) % 10 == 0:
            print(f'  {i+1}/{len(todo)}')
        time.sleep(0.3)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'  done')
