import argparse
import random

MODIFIERS_FILE = 'spell_modifiers.txt'
ESSENCES_FILE = 'spell_essences.txt'
FORMS_FILE = 'spell_forms.txt'
MODIFIERS_35_FILE = 'modifiers_35.txt'
ESSENCES_35_FILE = 'essences_35.txt'
FORMS_35_FILE = 'forms_35.txt'
VERB_FILE = 'verbs.txt'
ADJECTIVE_FILE = 'adjectives.txt'
ABSTRACT_NOUN_FILE = 'abstract_nouns.txt'
CONCRETE_NOUN_FILE = 'concrete_nouns.txt'

def ImportSpellKeywords():
    values = {}
    modifiers = open(MODIFIERS_FILE, 'r')
    essences = open(ESSENCES_FILE, 'r')
    forms_35 = open(FORMS_35_FILE, 'r')
    modifiers_35 = open(MODIFIERS_35_FILE, 'r')
    essences_35 = open(ESSENCES_35_FILE, 'r')
    forms = open(FORMS_FILE, 'r')
    verbs = open(ADJECTIVE_FILE, 'r')
    adjectives = open(VERB_FILE, 'r')
    abstract_nouns = open(ABSTRACT_NOUN_FILE, 'r')
    concrete_nouns = open(CONCRETE_NOUN_FILE, 'r')
    values['modifiers'] = [w.title() for w in modifiers.read().split('\n')]
    values['essences'] = [w.title() for w in essences.read().split('\n')]
    values['forms'] = [w.title() for w in forms.read().split('\n')]
    values['modifiers_35'] = [w.title() for w in modifiers_35.read().split('\n')]
    values['essences_35'] = [w.title() for w in essences_35.read().split('\n')]
    values['forms_35'] = [w.title() for w in forms_35.read().split('\n')]
    values['verbs'] = [w.title() for w in verbs.read().split('\n')]
    values['adjectives'] = [w.title() for w in adjectives.read().split('\n')]
    values['abstract_nouns'] = [w.title() for w in abstract_nouns.read().split('\n')]
    values['concrete_nouns'] = [w.title() for w in concrete_nouns.read().split('\n')]
    return values

def GenerateSpells(n=1, format=None):
    spell_keywords = ImportSpellKeywords()
    results = []
    for _ in range(n):
        results.append(GenerateSpell(spell_keywords, format))
    return results

'''
There are modifiers, essence nouns, and form nouns.
Example:
Modifier: Absorb
Essence: Stone
Form: Bolt

A spell can be:
* modifier + essence noun: Absorb Stone
* essence noun + form noun: Stone Bolt
Or, more esoterically:
* essence noun: Stone
* modifier + form noun: Absorb Bolt
* modifier + essence noun + form noun: Absorb Stone Bolt
'''
def GenerateSpellFormat():
    rand_form = random.random()
    format = ''
    if rand_form < 0.4:
        format = 'ME'
    elif rand_form < 0.8:
        format = 'EF'
    elif rand_form < 0.95:
        format = 'MF'
    elif rand_form < 0.975:
        format = 'MEF'
    elif rand_form < 0.99:
        format = 'E'
    elif rand_form < 0.995:
        format = 'MEE'
    else:
        format = 'EEF'
    return format

def GenerateBuckets(spellwords):
    probability_worse = 0.15
    probability_35 = 0.35
    modifiers = spellwords['modifiers']
    essences = spellwords['essences']
    forms = spellwords['forms']
    modifiers_35 = spellwords['modifiers_35']
    essences_35 = spellwords['essences_35']
    forms_35 = spellwords['forms_35']
    worse_modifiers = spellwords['verbs'] + spellwords['adjectives']
    worse_essences = spellwords['abstract_nouns']
    worse_forms = spellwords['concrete_nouns']

    local_modifiers = None
    r_mod = random.random()
    if r_mod < probability_worse:
        local_modifiers = worse_modifiers
    elif r_mod < probability_35 + probability_worse:
        local_modifiers = modifiers_35
    else:
        local_modifiers = modifiers

    local_essences = None
    e_mod = random.random()
    if e_mod < probability_worse:
        local_essences = worse_essences
    elif r_mod < probability_35 + probability_worse:
        local_essences = essences_35
    else:
        local_essences = essences

    local_forms = None
    r_mod = random.random()
    if r_mod < probability_worse:
        local_forms = worse_forms
    elif r_mod < probability_35 + probability_worse:
        local_forms = forms_35
    else:
        local_forms = forms

    return local_modifiers, local_essences, local_forms

def GenerateSpell(spellwords, spell_format=None):
    combine_nouns = True
    combination_probability = 0.8
    local_modifiers, local_essences, local_forms = GenerateBuckets(spellwords)
    prepositions = ['from', 'of', 'to', 'with']
    # if combine_nouns:
    #     modifiers += [f'{word} of' for word in spellwords['concrete_nouns']]
    #     forms += [f'of {word}' for word in spellwords['abstract_nouns']]
    if not spell_format:
        spell_format = GenerateSpellFormat()
    spell = ''
    prev_f = None
    for f in spell_format:
        local_modifiers, local_essences, local_forms = GenerateBuckets(spellwords)
        if f:
            spell += ' '
        if f == 'M':
            if combine_nouns:
                if random.random() < combination_probability:
                    spell += random.choice(local_modifiers)
                else:
                    spell += random.choice(local_forms) + ' ' + random.choice(prepositions)
            else:
                spell += random.choice(local_modifiers)
        elif f == 'E':
            if f == prev_f:
                spell += 'and '
            spell += random.choice(local_essences)
        elif f == 'F':
            if combine_nouns:
                r = random.random()
                if r < combination_probability:
                    spell += random.choice(local_forms)
                else:
                    spell += random.choice(prepositions) + ' ' + random.choice(local_essences)
            else:
                spell += random.choice(local_forms)
        prev_f = f

    if ' -' in spell:
        dashloc = spell.find(' -')
        spell = spell[:dashloc] + spell[dashloc+1:].lower()
    if '- ' in spell:
        dashloc = spell.find('- ')
        spell = spell[:dashloc+1] + spell[dashloc+2:]
    return spell

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--num_spells', '-n', dest='num_spells', nargs='?', type=int, default=1)
    parser.add_argument('--spell_format', '-f', dest='spell_format', nargs='?', type=str, default=None)
    args = parser.parse_args()
    print(f'Generating {args.num_spells} spell(s):')
    spells = GenerateSpells(args.num_spells, args.spell_format)
    for spell in spells:
        print(spell)


if __name__ == '__main__':
    main()
