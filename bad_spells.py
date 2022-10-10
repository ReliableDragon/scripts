import argparse
import random

MODIFIERS_FILE = 'spell_modifiers.txt'
ESSENCES_FILE = 'spell_essences.txt'
FORMS_FILE = 'spell_forms.txt'

def GenerateSpells(n=1):
    spell_keywords = ImportSpellKeywords()
    results = []
    for _ in range(n):
        results.append(GenerateSpell(spell_keywords))
    return results

def ImportSpellKeywords():
    values = {}
    modifiers = open(MODIFIERS_FILE, 'r')
    essences = open(ESSENCES_FILE, 'r')
    forms = open(FORMS_FILE, 'r')
    values['modifiers'] = modifiers.read().split('\n')
    values['essences'] = essences.read().split('\n')
    values['forms'] = forms.read().split('\n')
    return values

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
def GenerateSpell(spellwords):
    modifier = random.choice(spellwords['modifiers'])
    essence = random.choice(spellwords['essences'])
    form = random.choice(spellwords['forms'])
    rand_form = random.random()
    spell = ''
    if rand_form < 0.45:
        spell = modifier + ' ' + essence
    elif rand_form < 0.9:
        spell = essence + ' ' + form
    elif rand_form < 0.95:
        spell = modifier + ' ' + form
    elif rand_form < 0.975:
        spell = modifier + ' ' + essence + ' ' + form
    elif rand_form < 0.99:
        spell = essence
    elif rand_form < 0.995:
        spell = modifier + ' ' + essence + ' and ' + random.choice(spellwords['essences'])
    else:
        spell = essence + ' and ' + random.choice(spellwords['essences']) + ' ' + form
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
    args = parser.parse_args()
    print(f'Generating {args.num_spells} spell(s):')
    spells = GenerateSpells(args.num_spells)
    for spell in spells:
        print(spell)


if __name__ == '__main__':
    main()
