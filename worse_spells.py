import argparse
import random
import re
import os

class WorseSpells():
    
    FILEPATH = os.path.join(os.path.dirname(__file__), 'dictionaries/')
        # ('spell_modifiers.txt', 'modifiers'),
        # ('spell_essences.txt', 'essences'),
        # ('spell_forms.txt', 'forms'),
        # ('modifiers_35.txt', 'modifiers_35'),
        # ('essences_35.txt', 'essences_35'),
        # ('forms_35.txt', 'forms_35'),
        # ('modifiers_pf.txt', 'modifiers_pf'),
        # ('essences_pf.txt', 'essences_pf'),
        # ('forms_pf.txt', 'forms_pf'),
        # ('modifiers_gurps.txt', 'modifiers_gurps'),
        # ('essences_gurps.txt', 'essences_gurps'),
        # ('forms_gurps.txt', 'forms_gurps'),
        # ('modifiers_wordlist.txt', 'modifiers_wordlist'),
        # ('essences_wordlist.txt', 'essences_wordlist'),
        # ('forms_wordlist.txt', 'forms_wordlist'),
        # ('modifiers_middle_earth.txt', 'modifiers_middle_earth'),
        # ('essences_middle_earth.txt', 'essences_middle_earth'),
        # ('forms_middle_earth.txt', 'forms_middle_earth'),
        # ('modifiers_dict.txt', 'modifiers_dict'),
        # ('essences_dict.txt', 'essences_dict'),
        # ('forms_dict.txt', 'forms_dict'),

    # FILENAMES_AND_KEYWORDS = GenerateFilenamesAndKeywords()

    WEIGHTS_AND_FORMATS = [
        (400, 'ME'),
        (400, 'EF'),
        (150, 'MF'),
        (25, 'MEF'),
        (14, 'E'),
        (5, 'MEE'),
        (5, 'EEF'),
    ]

    WEIGHTS_AND_SUFFIXES = [
        # (15, '_dict'), # dictionary words
        (100, '_wordlist_nltk2'), # wordlist words
        (100, '_middle_earth_nltk2'), # Tolkien words
        (100, '_35'), # 3.5 spells
        (100, '_pf'), # pathfinder spells
        (100, '_gurps'), # gurps spells
        (100, ''), # 5e spells, no suffix for historical reasons
    ]

    FILE_SUFFIXES = [
        '35',
        'pf',
        'gurps',
        'wordlist',
        'middle_earth',
        'dict',
        'wordlist_nltk2',
    ]

    FORMAT_MAP = {'M': 'modifiers', 'E': 'essences', 'F': 'forms'}

    def __init__(self, spell_format=None, filter=None, filebase_override=None):
        self.spell_format = spell_format
        self.filter = filter
        self.word_sources = {}
        self.filebase_override = filebase_override
        self.filenames_and_keywords = self.GenerateFilenamesAndKeywords() 
        self.weights_and_suffixes = self.WEIGHTS_AND_SUFFIXES

        if self.filebase_override:
            print(f'Restricting search to {filebase_override}.')
            self.filenames_and_keywords = [
                (f'modifiers_{filebase_override}.txt', 'modifiers'),
                (f'essences_{filebase_override}.txt', 'essences'),
                (f'forms_{filebase_override}.txt', 'forms'),
            ]
            self.weights_and_suffixes = [(1, '')]

        self.filenames_and_keywords = [
            (os.path.join(self.FILEPATH, filename), keyword) 
            for filename, keyword in self.filenames_and_keywords]

        # print(self.filenames_and_keywords)
    
    def GenerateFilenamesAndKeywords(self):
        values = [ # hardcode exceptions to name pattern
            ('spell_modifiers.txt', 'modifiers'),
            ('spell_essences.txt', 'essences'),
            ('spell_forms.txt', 'forms'),
            ('verbs.txt', 'verbs'),
            ('adjectives.txt', 'adjectives'),
            ('abstract_nouns.txt', 'abstract_nouns'),
            ('concrete_nouns.txt', 'concrete_nouns'),
        ]
        suffixes = [a[1] for a in self.WEIGHTS_AND_SUFFIXES]
        for suffix in suffixes:
            if not suffix:
                # skip ''. I really should just refactor that one to match the format.
                continue 
            values.append((f'modifiers{suffix}.txt', f'modifiers{suffix}'))
            values.append((f'essences{suffix}.txt', f'essences{suffix}'))
            values.append((f'forms{suffix}.txt', f'forms{suffix}'))

        return values

    def GenerateSpells(self, n=1, filebase_override=None):
        self.ImportSpellKeywords(filebase_override)
        results = []
        for _ in range(n):
            results.append(self.GenerateSpell())
        return results

    def ImportSpellKeywords(self, filebase_override=None):
        for filename, keyword in self.filenames_and_keywords:
            with open(filename, 'r', encoding='utf-8') as file:
                self.word_sources[keyword] = [w.title() for w in file.read().split('\n')]
                if self.filter:
                    filtered = list(filter(lambda a: re.search(self.filter, a, re.I), self.word_sources[keyword]))
                    if filtered:
                        self.word_sources[keyword + '_filtered'] = filtered
        if self.filter and not any(['_filtered' in keyword for keyword in self.word_sources.keys()]):
            raise ValueError(f'No values matched filter "{self.filter}".')

    def GenerateSpell(self):
        prepositions = ['from', 'of', 'to', 'with']
        spell_format = self.spell_format
        if not spell_format:
            spell_format = self.GenerateSpellFormat()
        # If the spell format uses the same kind twice, they will always be drawn from the same bucket.
        # This makes filtering easier, and is a situation that only comes up rarely, but is suboptimal.
        buckets = self.GenerateBuckets(spell_format)

        spell = ''
        prev_f = None
        for f in spell_format:
            if f:
                spell += ' '
            if f == 'M':
                spell += random.choice(buckets['modifiers'])
            elif f == 'P':
                spell += random.choice(prepositions)
            elif f == 'E':
                if f == prev_f:
                    spell += 'and '
                spell += random.choice(buckets['essences'])
            elif f == 'F':
                spell += random.choice(buckets['forms'])
            else:
                raise ValueError(f'Got invalid spell format "{spell_format}".')
            prev_f = f

        if ' -' in spell:
            dashloc = spell.find(' -')
            spell = spell[:dashloc] + spell[dashloc+1:].lower()
        if '- ' in spell:
            dashloc = spell.find('- ')
            spell = spell[:dashloc+1] + spell[dashloc+2:]
        return spell

    def GenerateBuckets(self, spell_format):
        buckets = {}
        buckets['modifiers'] = self.GetRandomSpellListOfType('modifiers')
        buckets['essences'] = self.GetRandomSpellListOfType('essences')
        buckets['forms'] = self.GetRandomSpellListOfType('forms')

        if self.filter:
            possible_swaps = []
            for c in spell_format:
                if c in self.FORMAT_MAP and self.FORMAT_MAP[c] not in possible_swaps:
                        possible_swaps.append(self.FORMAT_MAP[c])

            random.shuffle(possible_swaps)

            swapped = False
            for swap in possible_swaps:
                filtered_bucket = self.GetRandomSpellListOfType(swap, filtered=True)
                if filtered_bucket:
                    swapped = True
                    buckets[swap] = filtered_bucket
                    break
            if not swapped:
                raise ValueError(f'Could not find valid swap for filter "{self.filter}".')

        return buckets

    def GetRandomSpellListOfType(self, base_type, filtered=False):
        weights_and_suffixes = self.weights_and_suffixes

        if filtered:
            # Filter out all suffixes corresponding to lists that have no values after filtering.
            weights_and_suffixes = [(weight, suffix + '_filtered') for weight, suffix in weights_and_suffixes 
                                    if base_type + suffix + '_filtered' in self.word_sources]
            if not weights_and_suffixes:
                return None

        suffix = self.WeightedRandomChoice(weights_and_suffixes)
        return self.word_sources[base_type + suffix]

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
        recombine_nouns = True
        recombination_probability = 0.05
        weights_and_formats = self.WEIGHTS_AND_FORMATS

        # Filter out formats that don't include at least one valid part if there's a filter.
        if self.spell_format:
            valid_format_parts = self.GetValidFormatParts()
            weights_and_formats = list(filter(
                lambda a: not valid_format_parts.isdisjoint(set(a[1])), weights_and_formats))
            if not weights_and_formats:
                raise ValueError(f'Filter of {self.filter} resulted in no valid auto-generated formats!')

        format = self.WeightedRandomChoice(weights_and_formats)

        # Do recombinations if enabled, after filtering out ones that would result in an invalid
        # format if there's a filter.
        # Technically there should be some check to see if the recombination would make the whole
        # format invalid, but that's difficult, especially since easy approaches would bias towards
        # changing the earlier symbols until the last change would make the format invalid.
        recombinations = {'M': 'FP', 'F': 'PM'}
        if self.spell_format:
            recombinations = {k: v for k, v in recombinations.items() if not valid_format_parts.isdisjoint(set(v))}
        for i, c in enumerate(format):
            if c in recombinations.keys() and recombine_nouns and random.random() < recombination_probability:
                format = format[:i] + recombinations[c] + format[i+1:]

        return format

    def WeightedRandomChoice(self, weights_and_values):
        weight_total = sum(i for i, _ in weights_and_values)
        # Pick a format via weighted random selection.
        r_mod = random.randint(1, weight_total)
        total = 0
        for weight, value in weights_and_values:
            total += weight
            if total >= r_mod:
                return value
        raise ValueError(f'Generated values of {r_mod}, which is not valid for choosing a format.')

    def GetValidFormatParts(self):
        valid_parts = set()
        for c, type in self.FORMAT_MAP.items():
            if any([part_list for part_list in self.word_sources if re.search(fr'{type}_.*_filtered', part_list)]):
                valid_parts.add(c)
        return valid_parts

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--num_spells', '-n', dest='num_spells', nargs='?', type=int, default=1)
    parser.add_argument('--spell_format', '-sf', dest='spell_format', nargs='?', type=str, default=None)
    parser.add_argument('--filter', '-f', dest='filter', nargs='?', type=str, default=None)
    parser.add_argument('--filebase_override', '-o', dest='filebase_override', type=str, default=None)
    args = parser.parse_args()
    print(f'Generating {args.num_spells} spell(s):')
    spell_generator = WorseSpells(args.spell_format, args.filter, args.filebase_override)
    spells = spell_generator.GenerateSpells(args.num_spells)
    for spell in spells:
        print(spell)


if __name__ == '__main__':
    main()
