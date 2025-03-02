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

#### NORMALIZZAZIONE TESTO

def roman_to_int(roman):
    """Converte un numero romano in un numero intero."""
    roman_numerals = {
        'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8,
        'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
        'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20
    }
    return roman_numerals.get(roman, roman)  # Ritorna l'intero o la stringa originale se non è un numero romano

def replace_abbreviations(text):
    """Sostituisce abbreviazioni comuni e normalizza i numeri ordinali e romani nel testo."""
    if not isinstance(text, str):  # Controllo per evitare errori con valori NaN o non stringhe
        return text

    replacements = {
        r"(?:(?<=\s)|(?<='))sen\.": "Senatore",
        r"(?:(?<=\s)|(?<='))on\.": "Onorevole",
        r"(?:(?<=\s)|(?<='))A\.? ?C\.?": "Atto Camera",
        r"(?:(?<=\s)|(?<='))n\.": "numero"
    }

    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Normalizzazione dei numeri ordinali (1° -> 1)
    text = re.sub(r"(\d{1,2})[°|ª](?=\s+[a-zA-Zà-ùÀ-Ù]+)", r"\1", text)

    # Sostituzione dei numeri romani con interi (solo quelli tra I e XX per sicurezza)
    text = re.sub(r"\b(I{1,3}|IV|V?I{0,3}|IX|X{1,2}|X?I{0,3})\b", 
                  lambda match: str(roman_to_int(match.group(0))), text)

    return text

### ACTIVITIES EXTRACTION - da cancellare ?

def find_activity_chunk_and_date(df_corpus, buffer, regex_chunk):
    results = []  # Lista per raccogliere i risultati
    
    regex_date = r"(\d{1,2})\s([a-zA-Zà-ùÀ-Ù]+)\s(\d{4})"
    
    for index, row in df_corpus.iterrows():
        sentences = row[buffer]  # Lista di frasi già estratte
        
        for sentence in sentences:
            # Cerca il match per 'presentato da' nella frase
            match = re.search(regex_chunk, sentence, re.IGNORECASE)
            
            if match:
                #print("Frase trovata:", sentence)  # Debug
                
                # Cerca la data nella stessa frase
                match_date = re.search(regex_date, sentence)
                
                # Aggiungi la tupla (id, presentato_da, data)
                results.append((
                    row['id'], 
                    match.group(0).strip(),
                    match_date.group(0).strip() if match_date else None
                ))
                
                # Una volta trovato, possiamo interrompere la ricerca in altre frasi
                break
    
    return results