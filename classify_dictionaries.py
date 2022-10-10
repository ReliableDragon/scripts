# import httplib2
import argparse
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

def main():
    dictionaryClassifier = DictionaryClassifier()
    dictionaryClassifier.ClassifyDictionaries()

class DictionaryClassifier():
    def __init__(self):
        self.found_modifiers = set()
        self.found_essences = set()
        self.found_forms = set()
        self.classifier = None

        self.classes = ['modifier', 'essence', 'form']
        self.nlp = spacy.load("en_core_web_md")

        modifiers = open(MODIFIERS_FILE, 'r')
        essences = open(ESSENCES_FILE, 'r')
        forms = open(FORMS_FILE, 'r')
        verbs = open(ADJECTIVE_FILE, 'r')
        adjectives = open(VERB_FILE, 'r')
        nouns = open(NOUN_FILE, 'r')

        self.training_modifiers = [w.lower() for w in modifiers.read().split('\n')]
        self.training_essences = [w.lower() for w in essences.read().split('\n')]
        self.training_forms = [w.lower() for w in forms.read().split('\n')]
        self.verbs = [w.title() for w in verbs.read().split('\n')]
        self.adjectives = [w.title() for w in adjectives.read().split('\n')]
        self.nouns = [w.title() for w in nouns.read().split('\n')]

        self.GetClassifier()

    def ClassifyDictionaries(self):
        dictionaries = self.verbs + self.adjectives + self.nouns
        print(f'Processing {len(dictionaries)} words.')
        i = 0
        for text in dictionaries:
            i += 1
            if i % 1000 == 0:
                print(f'Processed {i} words.')
            # tag_pairs = nltk.pos_tag(nltk.word_tokenize(text))
            token_text = self.nlp(text)
            for token in token_text:
                if token.pos_ in ['ADJ', 'VERB', 'NOUN']:
                    word_type = self.classes[self.classifier.predict([token.vector])[0]]
                    if word_type == 'modifier':
                        self.found_modifiers.add(token.text)
                    if word_type == 'essence':
                        self.found_essences.add(token.text)
                    if word_type == 'form':
                        self.found_forms.add(token.text)

        f = open('new_modifiers', 'w')
        f.write('\n'.join(self.found_modifiers))
        f.close()
        f = open('new_essences', 'w')
        f.write('\n'.join(self.found_essences))
        f.close()
        f = open('new_forms', 'w')
        f.write('\n'.join(self.found_forms))
        f.close()

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
    main()