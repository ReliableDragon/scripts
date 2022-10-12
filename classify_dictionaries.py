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
import numpy as np

MODIFIERS_FILE = 'spell_modifiers.txt'
ESSENCES_FILE = 'spell_essences.txt'
FORMS_FILE = 'spell_forms.txt'
VERB_FILE = 'verbs.txt'
ADJECTIVE_FILE = 'adjectives.txt'
NOUN_FILE = 'concrete_nouns.txt'

titles = {}

def main(filename_base, files_to_parse):
    dictionaryClassifier = DictionaryClassifier(filename_base)
    dictionaryClassifier.ClassifyDictionaries(files_to_parse)

class DictionaryClassifier():
    def __init__(self, filename_base):
        self.output = defaultdict(set)
        self.classifier = None
        self.filename_base = filename_base

        self.classes = ['modifiers', 'essences', 'forms']
        self.nlp = spacy.load("en_core_web_md")

        modifiers = open(MODIFIERS_FILE, 'r')
        essences = open(ESSENCES_FILE, 'r')
        forms = open(FORMS_FILE, 'r')

        self.training_modifiers = [w.lower() for w in modifiers.read().split('\n')]
        self.training_essences = [w.lower() for w in essences.read().split('\n')]
        self.training_forms = [w.lower() for w in forms.read().split('\n')]

        self.GetClassifier()

    def ClassifyDictionaries(self, files_to_parse):
        if not files_to_parse:
            raise ValueError(f'Didn\'t get any files to parse!')
        for filename in files_to_parse:
            with open(filename, 'r') as file:
                file = open(filename, 'r')
                words_to_classify = [w.lower() for w in file.read().split('\n')]
            print(f'Processing {len(words_to_classify)} words.')
        i = 0
        for word in words_to_classify:
            i += 1
            if i % 1000 == 0:
                print(f'Processed {i} words.')

            token_text = self.nlp(word)
            for token in token_text:
                if token.pos_ in ['ADJ', 'VERB', 'NOUN']:
                    probs = self.classifier.predict_proba([token.vector])[0] # First element, for first sample.
                    # formatted_probs = [f'{prob*10:.2f}' for prob in probs]
                    for prob, clazz in zip(probs, self.classes):
                        if prob > 0.05:
                            self.output[clazz].add(token.text)
                    # self.output.add(f'{token.text}: {formatted_probs}')

        for clazz, words in self.output.items():
            with open(f'{self.filename_base}_{clazz}.txt', 'w') as file:
                file.write('\n'.join(words))

    def GetClassifier(self):
        try:
            with open('pkl_classifier.pkl', 'rb') as file:
                self.classifier = pickle.load(file)
        except:
            print('No classifier found, regenerating.')

            train_set = [
                self.training_modifiers,
                self.training_essences,
                self.training_forms,
            ]
            X = np.stack([list(self.nlp(w))[0].vector for part in train_set for w in part])
            y = [label for label, part in enumerate(train_set) for _ in part]
            self.classifier = LogisticRegression(C=0.1, class_weight='balanced').fit(X, y)

            with open('pkl_classifier.pkl', 'wb') as file:
                pickle.dump(self.classifier, file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--files_to_parse', '-f', dest='files_to_parse', nargs='+', type=str)
    parser.add_argument('--filename_base', '-fn', dest='filename_base', nargs=1, type=str)
    args = parser.parse_args()
    print(args.files_to_parse)
    print(args.filename_base)
    exit()
