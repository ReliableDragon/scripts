import argparse
import random

MODIFIERS_FILE = 'spell_modifiers.txt'
ESSENCES_FILE = 'spell_essences.txt'
FORMS_FILE = 'spell_forms.txt'

def ImportSpellKeywords(filebase_override=None):
    values = {}
    if filebase_override:
        modifiers = open(f'{filebase_override}_modifiers.txt', 'r')
        essences = open(f'{filebase_override}_essences.txt', 'r')
        forms = open(f'{filebase_override}_forms.txt', 'r')
    else:
        modifiers = open(MODIFIERS_FILE, 'r')
        essences = open(ESSENCES_FILE, 'r')
        forms = open(FORMS_FILE, 'r')
    values['modifiers'] = modifiers.read().split('\n')
    values['essences'] = essences.read().split('\n')
    values['forms'] = forms.read().split('\n')
    return values

def GenerateSpells(n=1, format=None, filebase_override=None):
    spell_keywords = ImportSpellKeywords(filebase_override)
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


def GenerateSpell(spellwords, spell_format=None):
    combine_nouns = False
    modifiers = spellwords['modifiers']
    essences = spellwords['essences']
    forms = spellwords['forms']
    if combine_nouns:
        essences = essences + forms
        forms = essences
    if not spell_format:
        spell_format = GenerateSpellFormat()
    modifier = random.choice(modifiers)
    essence = random.choice(essences)
    form = random.choice(forms)
    rand_form = random.random()
    spell = ''
    prev_f = None
    for f in spell_format:
        if f:
            spell += ' '
        if f == 'M':
            spell += random.choice(modifiers)
        elif f == 'E':
            if f == prev_f:
                spell += 'and '
            spell += random.choice(essences)
        elif f == 'F':
            spell += random.choice(forms)
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
    parser.add_argument('--filebase_override', '-o', dest='filebase_override', type=str, default=None)
    args = parser.parse_args()
    print(f'Generating {args.num_spells} spell(s):')
    spells = GenerateSpells(args.num_spells, args.spell_format, args.filebase_override)
    for spell in spells:
        print(spell)


if __name__ == '__main__':
    main()
