import requests
from bs4 import BeautifulSoup
import csv
import time

def get_leggi(n: int,
              output_file: str = "normattiva_leggi.csv"):

    # Headers to simulate a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Base URL of Normattiva
    base_url = "https://www.normattiva.it"

    # Maximum number of document links to collect
    TARGET_LINKS = n 

    # List to store document links
    document_links: list[str] = []

    # Initialize session
    session = requests.Session()

    # Define the search URL
    search_url = f"{base_url}/ricerca/avanzata/0"

    # Page counter
    page_num = 0

    # Loop until the desired number of links is collected or no more pages exist
    while len(document_links) < TARGET_LINKS:
        current_page_url = f"{base_url}/ricerca/avanzata/{page_num}"
        print(f"Scraping: {current_page_url}")

        try:
            response = session.get(current_page_url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"Error loading page {current_page_url}, code: {response.status_code}")
                break

            # Parse HTML page
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract document links with "LEGGE" filter
            new_links = []
            for result in soup.find_all("div", class_="collapse-header"):
                title_element = result.find("a", class_="font-weight-semibold")
                if title_element and title_element.get_text(strip=True).upper().startswith("LEGGE"):
                    link = title_element["href"].strip()
                    if "caricaDettaglioAtto" in link:
                        new_links.append(base_url + link)

            # Add new unique links to the list
            for link in new_links:
                if link not in document_links:
                    document_links.append(link)
                    if len(document_links) >= TARGET_LINKS:
                        break

            print(f"Total collected links: {len(document_links)}")

            # Check for next page
            next_page_tag = next((a for a in soup.find_all("a") if "Successiva" in a.get_text(strip=True)), None)
            if not next_page_tag:
                print("No next page found. Stopping collection.")
                break

            # Increment page counter
            page_num += 1

        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            break

        # Pause to avoid blocks
        time.sleep(1)

    # Save results to a CSV file
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Document Link"])
        writer.writerows([[link] for link in document_links])

    print(f"\n {len(document_links)} 'LEGGE' links saved in {output_file}")
