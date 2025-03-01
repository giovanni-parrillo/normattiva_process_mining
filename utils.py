# TEXT MINING

import nltk
import re
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.util import ngrams
from collections import Counter

stop_words = set(stopwords.words('italian'))

def splitter_e_tokenizzatore(corpus):
    frasi = nltk.tokenize.sent_tokenize(corpus)
    tokens = []
    for frase in frasi:
        tokens_frase = nltk.tokenize.word_tokenize(frase)
        tokens.extend(tokens_frase)
    return frasi, tokens

def rimuovi_punteggiatura(tokens):
    tokens_no_punt = [token for token in tokens if re.match(r'\b[\w]+\b', token)]
    return tokens_no_punt

def rimuovi_stopwords(tokens):
    tokens_no_stopwords = [token for token in tokens if token.lower() not in stop_words]
    return tokens_no_stopwords

def extract_ngrams(text, n):
    # Tokenizza il testo
    tokens = word_tokenize(text.lower())
    
    # Filtra i tokens per rimuovere stopwords e caratteri non alfanumerici
    filtered_tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    
    # Genera i n-grammi
    n_grams = list(ngrams(filtered_tokens, n))
    
    return n_grams

def most_common_ngrams_corpus(dataset, n=2, top_n=30):
    all_ngrams = []
    
    # Itera sulla serie di testi
    for text in dataset:
        ngrams_in_text = extract_ngrams(text, n)
        all_ngrams.extend(ngrams_in_text)
    
    # Conta la frequenza degli n-grammi
    ngram_freq = Counter(all_ngrams)
    
    # Restituisce i top_n n-grammi più comuni
    return ngram_freq.most_common(top_n)

# Funzione per formattare e stampare gli n-grammi
def print_ngrams(ngrams):
    for ngram, freq in ngrams:
        print(f"{' '.join(ngram)}: {freq}")

# Funzione per estrarre chi ha presentato la proposta di legge usando REGEX "Proposto"
def extract_proposers(text):
    proposers = re.findall(r'Proposto da ([\w\s]+)', text)
    return proposers

####

def replace_abbreviations(text):
    """Sostituisce abbreviazioni comuni nel testo con le loro forme estese."""
    if not isinstance(text, str):  # Controllo per evitare errori con valori NaN o non stringhe
        return text

    replacements = {
        r"(?:(?<=\s)|(?<='))sen\.": "Senatore",
        r"(?:(?<=\s)|(?<='))on\.": "Onorevole",
        r"(?:(?<=\s)|(?<='))A\.? ?C\.?": "Atto Camera"
    }

    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Normalizzazione dei numeri ordinali (1° -> 1)
    text = re.sub(r"(\d{1,2})°(?=\s+[a-zA-Zà-ùÀ-Ù]+)", r"\1", text)

    return text

### ACTIVITIES EXTRACTION

