import argparse
import random

class WorseSpells():

    FILENAMES_AND_KEYWORDS = [
        ('spell_modifiers.txt', 'modifiers'),
        ('spell_essences.txt', 'essences'),
        ('spell_forms.txt', 'forms'),
        ('modifiers_35.txt', 'essences_35'),
        ('essences_35.txt', 'modifiers_35'),
        ('forms_35.txt', 'forms_35'),
        ('modifiers_pf.txt', 'modifiers_pf'),
        ('essences_pf.txt', 'essences_pf'),
        ('forms_pf.txt', 'forms_pf'),
        ('modifiers_dict.txt', 'modifiers_dict'),
        ('essences_dict.txt', 'essences_dict'),
        ('forms_dict.txt', 'forms_dict'),
        ('verbs.txt', 'verbs'),
        ('adjectives.txt', 'adjectives'),
        ('abstract_nouns.txt', 'abstract_nouns'),
        ('concrete_nouns.txt', 'concrete_nouns'),
    ]

    def __init__(self):
        self.spellwords = {}

    def ImportSpellKeywords(self):
        for filename, keyword in self.FILENAMES_AND_KEYWORDS:
            # print(f'Importing values from {filename}')
            with open(filename, 'r') as file:
                self.spellwords[keyword] = [w.title() for w in file.read().split('\n')]

        self.spellwords['modifiers_worse'] = self.spellwords['verbs'] + self.spellwords['adjectives']
        self.spellwords['essences_worse'] = self.spellwords['abstract_nouns']
        self.spellwords['forms_worse'] = self.spellwords['concrete_nouns']

    def GenerateSpells(self, n=1, format=None):
        self.ImportSpellKeywords()
        results = []
        for _ in range(n):
            results.append(self.GenerateSpell(format))
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
    def GenerateSpellFormat(self):
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

    def GetRandomBucket(self, base_type):
        weights_and_suffixes = [
            (15, '_dict'), # dictionary words
            (35, '_35'), # 3.5 spells
            (35, '_pf'), # pathfinder spells
            (35, ''), # 5e spells, no suffix for historical reasons
        ]
        weight_total = sum(i for i, _ in weights_and_suffixes)

        r_mod = random.randint(1, weight_total)
        total = 0
        for weight, suffix in weights_and_suffixes:
            total += weight
            if total >= r_mod:
                return self.spellwords[base_type + suffix]
        raise ValueError(f'Using r_mod of {r_mod}, somehow never reached a valid weight!')

    def GenerateBuckets(self):
        local_modifiers = self.GetRandomBucket('modifiers')
        local_essences = self.GetRandomBucket('essences')
        local_forms = self.GetRandomBucket('forms')

        return local_modifiers, local_essences, local_forms

    def GenerateSpell(self, spell_format=None):
        combine_nouns = True
        combination_probability = 0.1
        prepositions = ['from', 'of', 'to', 'with']
        if not spell_format:
            spell_format = self.GenerateSpellFormat()
        spell = ''
        prev_f = None
        for f in spell_format:
            local_modifiers, local_essences, local_forms = self.GenerateBuckets()
            if f:
                spell += ' '
            if f == 'M':
                if combine_nouns:
                    if random.random() < combination_probability:
                        spell += random.choice(local_forms) + ' ' + random.choice(prepositions)
                    else:
                        spell += random.choice(local_modifiers)
                else:
                    spell += random.choice(local_modifiers)
            elif f == 'E':
                if f == prev_f:
                    spell += 'and '
                spell += random.choice(local_essences)
            elif f == 'F':
                if combine_nouns:
                    if random.random() < combination_probability:
                        spell += random.choice(prepositions) + ' ' + random.choice(local_essences)
                    else:
                        spell += random.choice(local_forms)
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
    spell_generator = WorseSpells()
    spells = spell_generator.GenerateSpells(args.num_spells, args.spell_format)
    for spell in spells:
        print(spell)


if __name__ == '__main__':
    main()
