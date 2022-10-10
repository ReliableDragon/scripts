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

titles = {}

def main(site=None, maxDepth=2, restrictDomain=True):
    crawler = SiteCrawler(site, maxDepth, restrictDomain)
    crawler.CrawlSite()
    # CrawlSite(site, maxDepth, restrictDomain)

def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

class SiteCrawler():
    def __init__(self, site, maxDepth, restrictDomain):
        self.site = site
        self.maxDepth = maxDepth
        self.restrictDomain = restrictDomain
        self.abstract_nouns = {}
        self.found_modifiers = set()
        self.found_essences = set()
        self.found_forms = set()
        self.classifier = None

        self.classes = ['modifier', 'essence', 'form']
        self.nlp = spacy.load("en_core_web_md")

        modifiers = open(MODIFIERS_FILE, 'r')
        essences = open(ESSENCES_FILE, 'r')
        forms = open(FORMS_FILE, 'r')
        self.training_modifiers = [w.lower() for w in modifiers.read().split('\n')]
        self.training_essences = [w.lower() for w in essences.read().split('\n')]
        self.training_forms = [w.lower() for w in forms.read().split('\n')]
        self.GetClassifier()

    def CrawlSite(self):
        print(f'Crawling {self.site} with max depth {self.maxDepth}, and domain restriction set to {self.restrictDomain}.')
        http = urllib3.PoolManager()
        links = [(self.site, 0)]
        visitedPages = set()

        parsedUrl = urlparse(self.site)
        baseHost = parsedUrl.hostname
        baseUrl = parsedUrl.scheme + '://' + parsedUrl.hostname
        print(f'Base Host: {baseHost}')
        print(f'Base URL: {baseUrl}')

        while links:
            link, depth = links[0]
            links.pop(0)
            print(f'Processing page {link}.')

            parsedUrl = urlparse(link)
            visitedPages.add(link)
            if parsedUrl.hostname != baseHost and self.restrictDomain:
                print('Page is from a different domain, and domain is restricted. Skipping.')
                continue

            response = http.request('GET', link)
            soupPage = BeautifulSoup(response.data, "html.parser")
            newUrls = set()
            for link in soupPage.find_all('a', href=True):
                linkedUrl = link['href']
                # print(f'New link found: {linkedPage}')
                parsedLink = urlparse(linkedUrl)
                parsedLink = parsedLink._replace(fragment="")
                # print(f'Hostname: {parsedLink.hostname}')
                if not parsedLink.hostname:
                    linkedUrl = urljoin(baseUrl, parsedLink.geturl())
                    # print(f'Joined page: {linkedPage}')
                newUrls.add(linkedUrl)
            for url in newUrls:
                if link not in visitedPages and depth < self.maxDepth:
                    links.append((url, depth+1))

            texts = soupPage.findAll(text=True)
            texts = filter(tag_visible, texts)
            texts = [t.strip() for t in texts if t.strip()]
            self.ProcessText(texts)

            print(links)
            soupPage.decompose()

        f = open('new_modifiers', 'w')
        f.write('\n'.join(self.found_modifiers))
        f.close()
        f = open('new_essences', 'w')
        f.write('\n'.join(self.found_essences))
        f.close()
        f = open('new_forms', 'w')
        f.write('\n'.join(self.found_forms))
        f.close()
        # crawlPage(site, pageTitle, maxDepth, pages, links, restricted, siteBase)

    def ProcessText(self, texts):
        for text in texts:
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


# def crawlPage(site, title, maxDepth, pages, links, restricted = False, siteBase = ""):
    
#     try:
#         print("Crawling " + site + ", with maxDepth = " + str(maxDepth))
#         http = httplib2.Http()
#         status, response = http.request(site)

#         soupPage = BeautifulSoup(response, "html.parser", parse_only=SoupStrainer('a'))
#         for link in soupPage:
#             if link.has_attr('href'):
#                 linkedPage = link['href']
#                 linkedPage = urljoin(site, linkedPage)
#                 print("Getting title for " + linkedPage)
                
#                 try:
#                     if not linkedPage in titles:
#                         soup = BeautifulSoup(urllib2.urlopen(linkedPage), "html.parser")
#                         linkTitle = soup.title.string
#                         soup.decompose()
#                         #titles[linkedPage] = linkTitle
                        
#                     else:
#                         linkTitle = titles[linkedPage]

#                     links.add((title, linkTitle))
#                     if not linkTitle in pages and not "youtube" in linkedPage and not (restricted and not siteBase in linkedPage):
#                         pages.add(linkTitle)
#                         if (maxDepth > 1):
#                             crawlPage(linkedPage, linkTitle, maxDepth-1, pages, links, restricted, siteBase)

#                 except Exception as e:
#                     print("Error parsing " + linkedPage + "! {0}".format(e))
#                     links.add((title, linkedPage[linkedPage.find("http:\\")+7:]))
#                     if not linkedPage[linkedPage.find("http:\\")+7:] in pages and not (restricted and not siteBase in linkedPage):
#                         pages.add(linkedPage[linkedPage.find("http:\\")+7:])
#                         if (maxDepth > 1):
#                             crawlPage(linkedPage, linkTitle, maxDepth-1, pages, links, restricted, siteBase)

#                 #pages.add(linkedPage)
#         soupPage.decompose()
#     except Exception as e:
#         print ("Error on site " + site + ": {0}".format(e))
#     gc.collect()

# def getTitles(s):
#     returnSet = set()
#     for pair in s:
#         try:
#             soup = BeautifulSoup(urllib2.urlopen(pair[0]), "html.parser")
#             linkTitle1 = soup.title.string
#         except:
#             linkTitle1 = pair[0]
            
#         try:
#             soup = BeautifulSoup(urllib2.urlopen(pair[1]), "html.parser")
#             linkTitle2 = soup.title.string
#         except:
#             linkTitle2 = pair[1]
#         returnSet.add((linkTitle1, linkTitle2))
#     return returnSet


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--site', '-s', dest='site', nargs='?', type=str, default='http://tictactogether.gabesdemos.com/')
    parser.add_argument('--max_depth', '-d', dest='max_depth', nargs='?', type=int, default=2)
    parser.add_argument('--restrict_domain', '-r', dest='restrict_domain', nargs='?', type=bool, default=True)
    args = parser.parse_args()
    main(args.site, args.max_depth, args.restrict_domain)