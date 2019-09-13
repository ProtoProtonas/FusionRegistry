import os
import time
import xml.etree.ElementTree as et
import json
import nltk
import random
import matplotlib.pyplot as plt

from collections import Counter
from freg_funkcijos import openxml, print_xml, register_namespaces, remove_version_et, remove_version_str, sortCode
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def get_stem(word):
    possible_stems = []
    for stem in STEMS:
        if word.lower().startswith(stem):
            possible_stems.append(stem.lower())
    longest = ''
    for st in possible_stems:
        if len(st) > len(longest):
            longest = st.lower()

    if longest == '':
        return word

    return longest

TO_CHOP_OFF = [' ', '\n', '\t', '\r', '\xa0']
TO_DELETE = ['\t', '\r', '  ']
STEMS = []
STOP_WORDS = []

#with open('pilnas_zodynas.txt', 'r', encoding = 'utf-16') as f:
#    STEMS = (f.read()).split('\n')
#    STEMS.remove('')

#with open('zodynas/tik_įvardžiai.txt', 'r', encoding = 'utf-8-sig') as f:
#    STOP_WORDS = (f.read()).split('\n')

#with open('zodynas/stop_words.txt', 'r', encoding = 'utf-8-sig') as f:
#    STOP_WORDS += (f.read()).split('\n')

#STOP_WORDS = [get_stem(a) for a in STOP_WORDS]
#STOP_WORDS = list(set(STOP_WORDS))

def normalize_text(text_to_normalize):
    normalized_text = str(text_to_normalize)
    
    for symbol in TO_DELETE:
        if str(symbol) in normalized_text:
            normalized_text = normalized_text.replace(symbol, ' ')

    while normalized_text:
        if any(s == normalized_text[0] for s in TO_CHOP_OFF):
            normalized_text = normalized_text[1:]
        elif any(s == normalized_text[-1] for s in TO_CHOP_OFF):
            normalized_text = normalized_text[:-1]
        else:
            break

    while '  ' in normalized_text:
        normalized_text = normalized_text.replace('  ', ' ')

    return str(normalized_text)

def parse_codelist_to_text(codelist):
    texts = {'lt': [], 'en': []}
    for code in codelist:
        to_unpack = get_text(code)
        if to_unpack:
            t_lt, t_en = to_unpack
            texts['lt'].append(t_lt)
            texts['en'].append(t_en)

    return texts

def get_text(et):
    children = list(et)
    if len(children) == 0:
        return False
    lt_text = ''
    en_text = ''
    for ch in children:
        att = ch.attrib
        if 'lt' in att.values():
            lt_text = ch.text
        elif 'en' in att.values():
            en_text = ch.text

    return lt_text, en_text

def process_text(text):
    some_text = text
    some_text = some_text.replace('(', ' ')
    some_text = some_text.replace('/', ' ')
    some_text = some_text.replace('\\', ' ')
    some_text = some_text.replace(')', ' ')
    some_text = some_text.replace('"', ' ')
    some_text = some_text.replace('“', ' ')
    some_text = some_text.replace('„', ' ')
    some_text = some_text.replace('”', ' ')
    some_text = some_text.replace('+', ' ')
    some_text = some_text.replace('-', ' ')
    some_text = normalize_text(some_text)
    return some_text

def jaccard_similarity(text1, text2):
    text1 = process_text(text1)
    text2 = process_text(text2)

    words1 = text1.split(' ')
    words2 = text2.split(' ')
    new_words1 = [get_stem(a) for a in words1]
    new_words2 = [get_stem(a) for a in words2]
    
    local_stop_words = []
    for st in STOP_WORDS:
        if any(st == a for a in (new_words1 + new_words2)):
            local_stop_words.append(st)

    for stop_word in local_stop_words:
        for wd in new_words1:
            if wd == stop_word:
                new_words1.remove(wd)
        for wd in new_words2:
            if wd == stop_word:
                new_words2.remove(wd)

    all_words = list(set(new_words1).union(set(new_words2)))
    common_words = list(set(new_words1).intersection(set(new_words2)))
    if len(common_words) == 0 or len(all_words) == 0:
        return 0

    degree = len(common_words)/len(all_words)
    return degree

def cosine_similarity_lt(text1, text2):
    text1 = process_text(text1)
    text2 = process_text(text2)

    words1 = text1.split(' ')
    words2 = text2.split(' ')
    try:
        words1.remove('')
        words2.remove('')
    except:
        pass

    new_words1 = [get_stem(a) for a in words1]
    new_words2 = [get_stem(a) for a in words2]
    
    local_stop_words = []
    for st in STOP_WORDS:
        if any(st == a for a in (new_words1 + new_words2)):
            local_stop_words.append(st)

    for stop_word in local_stop_words:
        for wd in new_words1:
            if wd == stop_word:
                new_words1.remove(wd)
        for wd in new_words2:
            if wd == stop_word:
                new_words2.remove(wd)
    # jei kažkuris tekstas sudarytas vien iš stopwords ar dėl kokių nors priežasčių
    if len(new_words1) == 0 or len(new_words2) == 0:
        return 0

    words = {}
    for word in new_words1:
        if word not in words:
            words[word] = [1, 0]
        else:
            words[word][0] += 1
    for word in new_words2:
        if word not in words:
            words[word] = [0, 1]
        else:
            words[word][1] += 1

    a, b = (0, 0)
    sum = 0
    for val in words.values():
        a += val[0] * val[0]
        b += val[1] * val[1]
        sum += val[0] * val[1]

    #print(a, b, words, text1, text2)

    similarity = sum / (a**0.5 * b**0.5)
    return similarity

def cosine_similarity_en(text1, text2):
    text1 = process_text(text1)
    text2 = process_text(text2)

    lemmatizer = WordNetLemmatizer()

    words1 = word_tokenize(text1)
    words2 = word_tokenize(text2)
    try:
        words1.remove('')
        words2.remove('')
    except:
        pass

    new_words1 = [lemmatizer.lemmatize(a) for a in words1]
    new_words2 = [lemmatizer.lemmatize(a) for a in words2]
    
    local_stop_words = []
    for st in set(stopwords.words('english')):
        if any(st == a for a in (new_words1 + new_words2)):
            local_stop_words.append(st)

    for stop_word in local_stop_words:
        for wd in new_words1:
            if wd == stop_word:
                new_words1.remove(wd)
        for wd in new_words2:
            if wd == stop_word:
                new_words2.remove(wd)
    # jei kažkuris tekstas sudarytas vien iš stopwords ar dėl kokių nors priežasčių
    if len(new_words1) == 0 or len(new_words2) == 0:
        return 0

    words = {}
    for word in new_words1:
        if word not in words:
            words[word] = [1, 0]
        else:
            words[word][0] += 1
    for word in new_words2:
        if word not in words:
            words[word] = [0, 1]
        else:
            words[word][1] += 1

    a, b = (0, 0)
    sum = 0
    for val in words.values():
        a += val[0] * val[0]
        b += val[1] * val[1]
        sum += val[0] * val[1]

    #print(a, b, words, text1, text2)

    similarity = sum / (a**0.5 * b**0.5)

    return similarity
  
def compare_codelists(codelist1, codelist2):
    descriptions1 = parse_codelist_to_text(codelist1)
    descriptions2 = parse_codelist_to_text(codelist2)

    if len(codelist1) > 2 * len(codelist2) or len(codelist2) > 2 * len(codelist1):
        return 0.0
    if len(codelist1) > 150 or len(codelist2) > 150: 
        return 0.0

    for lang in ['en']:
        n = 0
        sim_sum = 0
        for desc1 in descriptions1[lang]:
            for desc2 in descriptions2[lang]:

                # čia pasirenkamas palyginimo būdas
                #sim = jaccard_similarity(desc1, desc2)
                sim = cosine_similarity_en(desc1, desc2)

                n += 1
                sim_sum += sim
    return sim_sum / n


def look_for_similarities():
    # reset stats for the file
    with open('stats.txt', 'w', encoding = 'utf-8') as f:
        f.write('')

    rt = openxml('new_final_codelist.xml')
    _, codelists = list(rt)
    for i, codelist in enumerate(codelists):
        print(len(codelist), '- length of', codelist.attrib['urn'].split('=')[-1])
        for j in range(i+1, len(codelists)):
            print('comparing codelists', codelist.attrib['urn'].split('=')[-1], codelists[j].attrib['urn'].split('=')[-1])
            similarity = compare_codelists(codelist, codelists[j])
            with open('stats.txt', 'a', encoding = 'utf-8') as f:
                f.write('%.5f ' % similarity)
                f.write(codelist.attrib['urn'].split('=')[-1] + ' ')
                f.write(codelists[j].attrib['urn'].split('=')[-1])
                f.write('\n')

    return 0

look_for_similarities()
