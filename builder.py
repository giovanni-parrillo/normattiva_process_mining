import normattiva_extractor
import search_normattiva
import csv

search_normattiva.get_leggi(100, "url_leggi.csv") # estrae il link di n leggi dalla pagina di ricerca
# Read links from the CSV file
with open("url_leggi.csv", newline="") as csvfile:
    reader = csv.reader(csvfile)
    links = [row[0] for row in reader if row] 

for link in links:
    normattiva_extractor.extract_normattiva_data(link, "normattiva_db.csv") # estrae i dati di n leggi e li salva in un file csv
    print(f"Data extracted from: {link}")

