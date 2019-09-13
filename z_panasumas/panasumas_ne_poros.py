
from freg_funkcijos import openxml, print_xml, register_namespaces
import nltk
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

STEMS = []
TO_CHOP_OFF = [' ', '\n', '\t', '\r', '\xa0']
TO_DELETE = ['\t', '\r', '  ']
STOP_WORDS = []

with open('pilnas_zodynas.txt', 'r', encoding = 'utf-16') as f:
    STEMS = (f.read()).split('\n')
    STEMS.remove('')

with open('zodynas/tik_įvardžiai.txt', 'r', encoding = 'utf-8-sig') as f:
    STOP_WORDS = (f.read()).split('\n')

with open('zodynas/stop_words.txt', 'r', encoding = 'utf-8-sig') as f:
    STOP_WORDS += (f.read()).split('\n')

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

STOP_WORDS = [get_stem(a) for a in STOP_WORDS]
STOP_WORDS = list(set(STOP_WORDS))

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

def get_wordnet_pos(treebank_tag): # returns part of speech

    if treebank_tag.startswith('J'):
        return wordnet.ADJ  # adjective
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV # adverb
    else:
        return wordnet.NOUN # default case

def cosine_similarity_lt(texts):
    texts = [process_text(text) for text in texts]
    words = []
    for text in texts:
        words.append(text.split(' '))

    new_texts = []
    for text in texts:
        new_text = [get_stem(a) for a in text.split(' ')]
        new_texts.append(new_text)
    
    local_stop_words = ['']

    all_words = []
    for txt in new_texts:
        all_words += txt
    all_words = set(all_words)

    for st in STOP_WORDS:
        if any(st == a for a in all_words):
            local_stop_words.append(st)

    for stop_word in local_stop_words:
        for txt in new_texts:
            for wd in txt:
                if wd == stop_word:
                    txt.remove(wd)

    # jei kažkuris tekstas sudarytas vien iš stopwords ar dėl kokių nors priežasčių
    if all(len(text) == 0 for text in new_texts):
        return 0

    words = {}
    len_texts = len(new_texts)

    for i, text in enumerate(new_texts):
        for word in text:
            if word not in words:
                words[word] = [0] * len_texts
                words[word][i] += 1
            else:
                words[word][i] += 1

    sum = 0
    total_len = [0] * len_texts

    for i, val in enumerate(words.values()):
        m = 1
        for j, a in enumerate(val):
            m *= a
            total_len[j] += a*a
        sum += m

    similarity = sum

    for leng in total_len:
        if leng != 0:
            similarity = similarity / (leng**0.5)

    return similarity
  
def cosine_similarity_en(texts):
    texts = [process_text(text) for text in texts]

    new_texts = []
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()

    # text is split into words and part of speech is marked for each word
    for text in texts:
        words = word_tokenize(text)
        tagged = nltk.pos_tag(words)

        for m, word_and_tag in enumerate(tagged):
            word, part_of_speech = word_and_tag

            w = lemmatizer.lemmatize(word, get_wordnet_pos(part_of_speech)) # word is turned back into its original (simplified) form
            # check if the word has any meaning at all (or if it is a word at all)
            if w not in stop_words:
                if w not in """,...()'":-;''``""":
                    words[m] = w

        new_texts.append(words)

    #print(new_texts)
    # jei kažkuris tekstas sudarytas vien iš stopwords ar dėl kokių nors priežasčių
    if all(len(text) == 0 for text in new_texts):
        return 0

    words = {}
    len_texts = len(new_texts)

    for i, text in enumerate(new_texts):
        for word in text:
            if word not in words:
                words[word] = [0] * len_texts
                words[word][i] += 1
            else:
                words[word][i] += 1

    sum = 0
    total_len = [0] * len_texts

    for i, val in enumerate(words.values()):
        m = 1
        for j, a in enumerate(val):
            m *= a
            total_len[j] += a*a
        sum += m

    similarity = sum

    for leng in total_len:
        if leng != 0:
            similarity = similarity / (leng**0.5)

    return similarity

def get_pairs():
    threshold = 0.01

    with open('stats_sorted.txt', 'r') as f:
        file = f.read()
        file = file.split('\n')

    similar = {}


    for line in file:
        try:
            sim, name1, name2 = line.split(' ')
            if float(sim) >= threshold:
                if name1 in similar:
                    similar[name1].append(name2)
                else:
                    similar[name1] = [name2]

                if name2 in similar:
                    similar[name2].append(name1)
                else:
                    similar[name2] = [name1]
        except:
            pass

    return similar

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


def main():
    rt = openxml('new_final_codelist.xml')
    _, codelists = list(rt)
    pairs = get_pairs()
    similar_keys = []
    
    with open('panasus.txt', 'w', encoding = 'utf-8') as f:
        f.write('')

    for key in pairs:
        similar_keys.append(pairs[key] + [key])

    for keygroup in similar_keys:
        similar_codelists = []
        for i, codelist in enumerate(codelists):
            if any(id in codelist.attrib['urn'] for id in keygroup):
                similar_codelists.append(parse_codelist_to_text(codelist)['en'][0])

        sim = cosine_similarity_en(similar_codelists)
        if sim > 0:
            for codelist in similar_codelists:
                print(process_text(codelist))
            print(keygroup)
            print(sim)
            print('\n\n\n')
            with open('panasus.txt', 'a', encoding = 'utf-8') as f:
                for codelist in similar_codelists:
                    f.write(process_text(codelist) + '\n')
                f.write(str(keygroup) + '\n')
                f.write(str(sim) + '\n')
                f.write('\n')
            

    return 0

main()

