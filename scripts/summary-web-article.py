#! /usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from heapq import nlargest
import sys


url = sys.argv[1]
response = requests.get(url)
html_content = response.text

soup = BeautifulSoup(html_content, "html.parser")
article_text = ""
for element in soup.select("article p"):
    article_text += "\n" + element.text

sentences = sent_tokenize(article_text)
stop_words = set(stopwords.words("english"))
word_frequencies = FreqDist()
for word in nltk.word_tokenize(article_text):
    if word.lower() not in stop_words:
        word_frequencies[word.lower()] += 1


sentence_scores = {}
for sentence in sentences:
    for word in nltk.word_tokenize(sentence.lower()):
        if word in word_frequencies.keys():
            if len(sentence.split(" ")) < 30:
                if sentence not in sentence_scores.keys():
                    sentence_scores[sentence] = word_frequencies[word]
                else:
                    sentence_scores[sentence] += word_frequencies[word]


summary_sentences = nlargest(5, sentence_scores, key=sentence_scores.get)
summary = " ".join(summary_sentences)

print('Summary:', summary)

if len(summary) > 10:
    from googletrans import Translator

    translator = Translator(service_urls=['translate.google.com'])
    text = summary
    translated = translator.translate(text, src='en', dest='pt')

    print('Tradução:', translated.text)


