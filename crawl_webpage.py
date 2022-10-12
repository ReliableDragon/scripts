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

titles = {}

def main(site, output_file, maxDepth=2, restrictDomain=True):
    crawler = SiteCrawler(site, output_file, maxDepth, restrictDomain)
    crawler.CrawlSite()

def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

class SiteCrawler():
    def __init__(self, site, output_file, maxDepth, restrictDomain):
        self.site = site
        self.output_file = output_file
        self.maxDepth = maxDepth
        self.restrictDomain = restrictDomain
        self.output = set()

        self.nlp = spacy.load("en_core_web_md")

    def CrawlSite(self):
        print(f'Crawling {self.site} with max depth {self.maxDepth}, and domain restriction set to {self.restrictDomain}.')
        http = urllib3.PoolManager()
        links = [(self.site, 0)]
        hashedLinks = {self.site}
        # visitedPages = set()

        parsedUrl = urlparse(self.site)
        baseHost = parsedUrl.hostname
        baseUrl = parsedUrl.scheme + '://' + parsedUrl.hostname
        print(f'Base Host: {baseHost}')
        print(f'Base URL: {baseUrl}')

        while links:
            link, current_depth = links[0]
            links.pop(0)
            print(f'Processing page {link}.')

            response = http.request('GET', link)
            soupPage = BeautifulSoup(response.data, "html.parser")
            newUrls = set()
            for link in soupPage.find_all('a', href=True):
                # print(f'Evaluating link {link}')
                linkedUrl = link['href']
                # print(f'Evaluating linkedUrl {linkedUrl}')
                # print(f'New link found: {linkedPage}')
                parsedLink = urlparse(linkedUrl)
                parsedLink = parsedLink._replace(fragment="")
                # print(f'parsedLink: {parsedLink}, hostname: {parsedLink.hostname}, has_hostname: {bool(parsedLink.hostname)}, restrict_domain: {self.restrictDomain}')
                # print(f'Hostname: {parsedLink.hostname}')
                if parsedLink.scheme and (parsedLink.scheme not in ['http', 'https']):
                    # print(f'Skipping non-http scheme {parsedLink.scheme}!')
                    continue
                if not parsedLink.hostname:
                    linkedUrl = urljoin(baseUrl, parsedLink.geturl())
                    parsedLink = urlparse(linkedUrl)
                    # print(f'Joined page: {linkedPage}')
                if  self.restrictDomain and (parsedLink.hostname != baseHost):
                    # print('Page is from a different domain, and domain is restricted. Skipping.')
                    continue
                if linkedUrl in hashedLinks:
                    continue
                # print('Adding url!')
                newUrls.add(linkedUrl)
            for url in newUrls:
                if url not in hashedLinks and current_depth < self.maxDepth:
                    hashedLinks.add(url)
                    links.append((url, current_depth+1))

            texts = soupPage.findAll(text=True)
            texts = filter(tag_visible, texts)
            texts = [t.strip() for t in texts if t.strip()]
            self.ProcessText(texts)

            print(f'Remaining: {len(links)}')
            soupPage.decompose()

        with open(os.path.join(DICT_FILEPATH, self.output_file), 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.output))

    def ProcessText(self, texts):
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
                self.output.add(f'{text},{pos}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--site', '-s', dest='site', nargs='?', type=str, default='http://tictactogether.gabesdemos.com/')
    parser.add_argument('--output_file', '-o', dest='output_file', type=str)
    parser.add_argument('--max_depth', '-d', dest='max_depth', nargs='?', type=int, default=2)
    parser.add_argument('--restrict_domain', '-r', dest='restrict_domain',  action=argparse.BooleanOptionalAction, type=bool, default=True)
    args = parser.parse_args()
    main(args.site, args.output_file, args.max_depth, args.restrict_domain)