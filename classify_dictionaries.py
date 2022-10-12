# import httplib2
import argparse
from collections import defaultdict
import urllib3
from bs4 import BeautifulSoup, SoupStrainer, Comment
import os
import urllib.request as urllib2
from urllib.parse import urljoin
from urllib.parse import urlparse
import gc
import nltk
import pickle


import spacy
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.multioutput import MultiOutputClassifier
import numpy as np

VERB_FILE = 'verbs.txt'
ADJECTIVE_FILE = 'adjectives.txt'
NOUN_FILE = 'concrete_nouns.txt'

DICT_FILEPATH = os.path.join(os.path.dirname(__file__), 'dictionaries/')
CLASSIFIER_FILEPATH = os.path.join(os.path.dirname(__file__), 'classifiers/')

MODIFIERS_FILE = os.path.join(DICT_FILEPATH, 'spell_modifiers.txt')
ESSENCES_FILE = os.path.join(DICT_FILEPATH, 'spell_essences.txt')
FORMS_FILE = os.path.join(DICT_FILEPATH, 'spell_forms.txt')

VALID_TAGS = [
    'JJ',
    'JJR',
    'JJS',
    'NN',
    'VB',
    'VBG',
    'VBP',
]


titles = {}

def main(output_filename_base, files_to_parse, debug=False, predict_probs=False, is_tokenized=False):
    dictionaryClassifier = DictionaryClassifier(output_filename_base, debug, predict_probs, is_tokenized)
    dictionaryClassifier.ClassifyDictionaries(files_to_parse)

class DictionaryClassifier():
    def __init__(self, output_filename_base, debug=False, predict_probs=False, is_tokenized=False):
        self.output = defaultdict(set)
        self.classifier = None
        self.output_filename_base = output_filename_base
        self.debug = debug
        self.predict_probs = predict_probs
        self.is_tokenized = is_tokenized

        self.classes = ['modifiers', 'essences', 'forms']
        self.nlp = spacy.load("en_core_web_md")

        self.GetClassifier()

    def GetWordsAndTags(self, text):
        words_and_tags = set()
        lines = text.split('\n')
        for line in lines:
            if self.is_tokenized:
                word, tag = line.split(',')
                word = word.lower()
            else:
                word = line.lower()
                try:
                    tag = nltk.pos_tag([word])[0][1]
                except:
                    raise ValueError(f'Got word that couldn\'t be tagged: {word}.')
            words_and_tags.add((word, tag))

        return words_and_tags

    def ClassifyDictionaries(self, files_to_parse):
        if not files_to_parse:
            raise ValueError(f'Didn\'t get any files to parse!')
        words_to_classify = []
        for filename in files_to_parse:
            filename = os.path.join(DICT_FILEPATH, filename)
            with open(filename, 'r', encoding='utf-8') as file:
                words_to_classify = self.GetWordsAndTags(file.read())
                # words_to_classify += [w.lower() for w in file.read().split('\n')]
        print(f'Processing {len(words_to_classify)} words.')
        i = 0
        for word, tag in words_to_classify:
            i += 1
            if i % 1000 == 0:
                print(f'Processed {i} words.')

            token_text = self.nlp(word)
            for token in token_text:
                    if tag not in VALID_TAGS:
                        continue

                    # First element, for first sample.
                    if self.predict_probs:
                        probs = self.classifier.predict_proba([token.vector])
                    else:
                        probs = self.classifier.predict([token.vector])

                    if self.debug:
                        # formatted_probs = [f'{prob*100:.2f}' for prob in probs]
                        self.output['debug'].add(f'{token.text}: {probs}')
                    else:

                        # Multilabel approach
                        for prob, clazz in zip(probs, self.classes):
                            text = token.text
                            if tag:
                                if clazz == 'modifiers':
                                    if token.pos_ == 'NOUN':
                                        text += ' of'
                                if clazz == 'essences':
                                    if tag in ['JJ', 'JJR', 'JJS', 'VB', 'VBP'] or token.pos_ == 'ADJ':
                                        continue # essences should not be adjectives or non-gerund verbs
                                if clazz == 'forms':
                                    if tag in ['JJ', 'JJR', 'JJS'] or token.pos_ == 'ADJ':
                                        continue # forms should not be adjectives
                            if self.predict_probs:
                                prob = prob[0] # Unnest array
                                _, prob = prob # Use true prob, discard false prob
                            if prob > 0.5:
                                self.output[clazz].add(text)

        # Write output
        for clazz, words in self.output.items():
            filename = os.path.join(DICT_FILEPATH, f'{clazz}_{self.output_filename_base}.txt')
            with open(filename, 'w', encoding='utf-8') as file:
                file.write('\n'.join(words))

    def GetClassifier(self):
        filename = os.path.join(CLASSIFIER_FILEPATH, 'pkl_classifier_multioutputclassifier.pkl')
        try:
            with open(filename, 'rb') as file:
                self.classifier = pickle.load(file)
                # print(f'Is Multilabel: {self.classifier.multilabel_}')
        except:
            print('No classifier found, regenerating.')

            modifiers = open(MODIFIERS_FILE, 'r', encoding='utf-8')
            essences = open(ESSENCES_FILE, 'r', encoding='utf-8')
            forms = open(FORMS_FILE, 'r', encoding='utf-8')

            training_modifiers = [w.lower() for w in modifiers.read().split('\n')]
            training_essences = [w.lower() for w in essences.read().split('\n')]
            training_forms = [w.lower() for w in forms.read().split('\n')]

            train_set = [
                training_modifiers,
                training_essences,
                training_forms,
            ]
            X = np.stack([list(self.nlp(w))[0].vector for fragment_list in train_set for w in fragment_list])
            y = [
                [word in training_modifiers, word in training_essences, word in training_forms] 
                for label, fragment_list in enumerate(train_set) for word in fragment_list
                ]
            # print(y[:10])
            # exit()
            logistic_regression = LogisticRegression(
                C=0.1, class_weight='balanced', max_iter=1000, multi_class='ovr')
            logistic_regression = MultiOutputClassifier(logistic_regression)
            logistic_regression = logistic_regression.fit(X, y)
            self.classifier = logistic_regression
            # print(f'Is Multilabel: {self.classifier.multilabel_}')

            with open(filename, 'wb') as file:
                pickle.dump(self.classifier, file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--files_to_parse', '-f', dest='files_to_parse', nargs='+', type=str)
    parser.add_argument('--output_filename_base', '-o', dest='output_filename_base', type=str)
    parser.add_argument('--debug', dest='debug', type=bool, action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument('--predict_probs', dest='predict_probs', type=bool, action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument('--is_tokenized', dest='is_tokenized', type=bool, action=argparse.BooleanOptionalAction, default=False)
    args = parser.parse_args()
    print(args.files_to_parse)
    print(args.output_filename_base)
    main(args.output_filename_base, args.files_to_parse, args.debug, args.predict_probs, args.is_tokenized)