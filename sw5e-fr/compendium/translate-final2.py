#!/usr/bin/env python3
"""Final targeted pass: only translate truly English text remaining."""
import json, os, re, sys, time, requests

SRC = r'C:\Users\QuentinGENSE\OneDrive - Airflux\Documents\Projet\Module_Traduction_ST5e\sw5e-fr\compendium'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
TL_URL = 'https://translate.googleapis.com/translate_a/single'

ac = re.compile(r'[àâçéèêëîïôûùüÿœ]', re.I)

# English-only words that definitively indicate untranslated text  
EN_ONLY = re.compile(r'\b(the|you|your|when|gain|have|make|deal|hit|save|once|per|each|minute|hour|round|attack|damage|creature|target|bonus|action|reaction|feature|ability|level|check|throw|point|power|range|weapon|armor|class|increase|decrease|choose|spend|instead|other|another|number|equal|twice|times|proficient|fighting|martial|style|mastery|form|stance|technique|practice|approach|pursuit|specialist|order|engineering|path|way|until|during|before|after|while|within|without|unless|whether|both|more|less|than|then|also|must|may|cannot|can|use|using|used|make|making|made|gain|gains|gained|gaining|deal|deals|dealt|dealing|hit|hits|hitting|add|adds|added|adding|roll|rolls|rolled|rolling|reduce|reduces|reduced|reducing)\b', re.I)

FR_WORDS = {
    'force', 'sagesse', 'charisme', 'constitution', 'intelligence', 'dexterite',
    'maitrise', 'modificateur', 'reaction', 'degats', 'sauvegarde',
    'classe', 'armure', 'action', 'bonus', 'repos', 'court', 'long',
    'points', 'vie', 'des', 'de', 'jet', 'niveau', 'tour', 'pouvoir',
    'technique', 'aptitude', 'capacite', 'effet', 'cible', 'creature',
    'avantage', 'desavantage', 'metres', 'minute', 'soins',
    'attaque', 'arme', 'distance', 'corps',
    'test', 'caracteristique', 'score',
    'personnelle', 'contact', 'categorie',
    'concentration', 'duree', 'portee',
    'zone', 'cone', 'rayon', 'ligne',
    'volonte', 'moitie', 'aucun',
    'physique', 'mental', 'social',
    'combat', 'style', 'forme',
    'don', 'particularite', 'espece',
    'vaisseau', 'etoile', 'deploiement',
    'invocation', 'pouvoir', 'technologique',
    'amelioration', 'modification', 'equipement',
    'munition', 'explosif', 'grenade',
    'charge', 'mine', 'thermique',
    'jetpack', 'paquetage',
    'tranchant', 'perforant', 'contondant',
    'acide', 'froid', 'feu', 'force', 'foudre',
    'necrotique', 'poison', 'psychique', 'radiant', 'tonnerre',
    'kirath', 'ossan', 'jabiim', 'kiribian', 'melodie',
    'rythme', 'harmonie', 'cacophonie', 'silence',
    'sabre', 'laser', 'vibro', 'blaster',
    'bouclier', 'armure', 'casque',
    'ceinture', 'bottes', 'gants',
    'cape', 'tenue', 'uniforme',
    'droid', 'droide', 'protocole', 'astromech',
    'biotech', 'cybertech', 'armstech', 'armormech',
    'gadget', 'explosif', 'informatique',
    'piratage', 'securite', 'outil',
    'kit', 'medic', 'medpac', 'kolto',
    'bacta', 'stimulant', 'antidote',
    'ralentir', 'paralysie', 'petrification',
    'empoisonnement', 'maladie', 'fatigue',
    'epuisement', 'inconscient', 'assourdi',
    'aveugle', 'charme', 'effraye',
    'entrave', 'etourdi', 'invisible',
    'a terre', 'agrippe',
    'maitrises', 'competence', 'outil',
    'armes', 'armure', 'langue',
    'alignement', 'taille', 'vitesse',
    'age', 'type', 'langues',
}

def is_english(text):
    """Check if text is actually English (not French without accents)."""
    if not text or len(text.strip()) < 3:
        return False
    if ac.search(text):
        return False
    
    # Must have English-only words
    if not EN_ONLY.search(text.lower()):
        return False
    
    # Count French words
    words = re.findall(r"[a-z]+", text.lower())
    if not words:
        return False
    fr_count = sum(1 for w in words if w in FR_WORDS)
    fr_ratio = fr_count / len(words)
    
    # If many French words, it's already translated
    return fr_ratio < 0.3


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
        for field in ('name', 'description'):
            text = (entry.get(field, '') or '').strip()
            if is_english(text):
                todo.append((key, field))
    
    if not todo:
        continue
    
    print(f'{fn}: {len(todo)} EN texts')
    for i, (key, field) in enumerate(todo):
        text = entries[key][field]
        translated = translate_one(text)
        if translated and translated != text:
            entries[key][field] = translated
        total += 1
        time.sleep(0.15)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

print(f'\nDone! {total} truly English texts translated')
