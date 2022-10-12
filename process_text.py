
import argparse
import os
import nltk


DICT_FILEPATH = os.path.join(os.path.dirname(__file__), 'dictionaries/')

VALID_TAGS = [
    'JJ',
    'JJR',
    'JJS',
    'NN',
    'VB',
    'VBG',
    'VBP',
]

def ProcessTextFile(input_files, output_filename):
    output = set()
    for filename in input_files:
        with open(os.path.join(DICT_FILEPATH, filename), 'r', encoding='utf-8') as f:
            text = f.read()
            sentence_tokens = nltk.sent_tokenize(text)
            output.update(ProcessText(sentence_tokens))
    with open(os.path.join(DICT_FILEPATH, output_filename), 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
        

def ProcessText(texts):
    output = set()
    i = 0
    for text in texts:
        i += 1
        if i % 1000 == 0:
            print(f'Processed {i} text fragments.')
        # tag_pairs = nltk.pos_tag(nltk.word_tokenize(text))
        token_text = nltk.word_tokenize(text)
        tagged_text = nltk.pos_tag(token_text)
        # token_text = self.nlp(text)
        for token in tagged_text:
            # if token.pos_ in ['ADJ', 'VERB', 'NOUN']:
            text = token[0]
            pos = token[1]
            if pos not in VALID_TAGS:
                continue
            if not text.isalpha():
                continue
            output.add(f'{text},{pos}')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_file', '-o', dest='output_file', type=str)
    parser.add_argument('--input_files', '-i', dest='input_files', nargs='+', type=str)
    args = parser.parse_args()
    ProcessTextFile(args.input_files, args.output_file)