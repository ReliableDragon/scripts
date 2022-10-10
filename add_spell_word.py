

ESSENCES_FILE = 'spell_essences.txt'
FORMS_FILE = 'spell_forms.txt'
MODIFIERS_FILE = 'spell_modifiers.txt'

def main():
    line = ''
    while line != 'exit':
        type = ''
        while type.lower() not in ['e', 'essence', 'm', 'modifier', 'f', 'form']:
            type = input('What kind of spell word is this? (Modifier, Essence, Form)\n')
        if type.lower() == 'exit':
            break

        f = get_file(type, 'r')
        filetext = f.read()
        f.close()

        spellword = input('Input spellword:\n')
        spellword = spellword.title()

        spellwords = filetext.strip().split('\n')
        if spellword in spellwords:
            print('Spellword already present!')
            continue
        spellwords.append(spellword)
        spellwords = sorted(spellwords)

        f = get_file(type, 'w')
        f.write('\n'.join(spellwords))
        f.close()

def get_file(type, mode):
    if type.lower() in ['e', 'essence']:
        f = open(ESSENCES_FILE, mode)
    if type.lower() in ['f', 'form']:
        f = open(FORMS_FILE, mode)
    if type.lower() in ['m', 'modifier']:
        f = open(MODIFIERS_FILE, mode)
    return f

if __name__ == '__main__':
    main()