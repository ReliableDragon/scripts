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


titles = {}

def main(filename_base, files_to_parse, debug=False, predict_probs=False):
    dictionaryClassifier = DictionaryClassifier(filename_base, debug, predict_probs)
    dictionaryClassifier.ClassifyDictionaries(files_to_parse)

class DictionaryClassifier():
    def __init__(self, filename_base, debug=False, predict_probs=False):
        self.output = defaultdict(set)
        self.classifier = None
        self.filename_base = filename_base
        self.debug = debug
        self.predict_probs = predict_probs

        self.classes = ['modifiers', 'essences', 'forms']
        self.nlp = spacy.load("en_core_web_md")

        modifiers = open(MODIFIERS_FILE, 'r', encoding='utf-8')
        essences = open(ESSENCES_FILE, 'r', encoding='utf-8')
        forms = open(FORMS_FILE, 'r', encoding='utf-8')

        self.training_modifiers = [w.lower() for w in modifiers.read().split('\n')]
        self.training_essences = [w.lower() for w in essences.read().split('\n')]
        self.training_forms = [w.lower() for w in forms.read().split('\n')]

        self.GetClassifier()

    def ClassifyDictionaries(self, files_to_parse):
        if not files_to_parse:
            raise ValueError(f'Didn\'t get any files to parse!')
        words_to_classify = []
        for filename in files_to_parse:
            filename = os.path.join(DICT_FILEPATH, filename)
            with open(filename, 'r', encoding='utf-8') as file:
                words_to_classify += [w.lower() for w in file.read().split('\n')]
        print(f'Processing {len(words_to_classify)} words.')
        i = 0
        for word in words_to_classify:
            i += 1
            if i % 1000 == 0:
                print(f'Processed {i} words.')

            token_text = self.nlp(word)
            for token in token_text:
                if token.pos_ in ['ADJ', 'VERB', 'NOUN']:
                    tag = None
                    try:
                        tag = nltk.pos_tag([token.text])[0][1]
                        skip_tags = [
                            'NNS', # plural nouns
                            'NNP', # proper nouns
                            'NNPS', # plural proper nouns
                            'VBD', # past tense
                            'VBN', # past participle
                            'VBZ', # third-person singular present verbs
                        ]
                        if tag in skip_tags:
                            continue
                    except:
                        raise ValueError(f'Got token that couldn\'t be tagged: {token}.')
                    # First element, for first sample.
                    if self.predict_probs:
                        probs = self.classifier.predict_proba([token.vector])
                    else:
                        probs = self.classifier.predict([token.vector])
                    if self.debug:
                        # formatted_probs = [f'{prob*100:.2f}' for prob in probs]
                        self.output['debug'].add(f'{token.text}: {probs}')
                    else:
                        # Non-multilabel approach
                        # for prob, clazz in zip(probs, self.classes):
                        #     if prob*100 > 25:
                        #         self.output[clazz].add(token.text)

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

        for clazz, words in self.output.items():
            filename = os.path.join(DICT_FILEPATH, f'{clazz}_{self.filename_base}.txt')
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

            train_set = [
                self.training_modifiers,
                self.training_essences,
                self.training_forms,
            ]
            X = np.stack([list(self.nlp(w))[0].vector for fragment_list in train_set for w in fragment_list])
            y = [
                [word in self.training_modifiers, word in self.training_essences, word in self.training_forms] 
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
    parser.add_argument('--filename_base', '-fn', dest='filename_base', type=str)
    parser.add_argument('--debug', dest='debug', type=bool, action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument('--predict_probs', dest='predict_probs', type=bool, action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    print(args.files_to_parse)
    print(args.filename_base)
    main(args.filename_base, args.files_to_parse, args.debug, args.predict_probs)