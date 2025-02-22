import csv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
import logging
import time
import requests
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_main_page_info(main_page_url: str):
    """
    Fetches basic info from the main page:
    - Number of articles
    - Full-text URL (from "visualizza atto intero" button)
    """
    base_url = "https://www.normattiva.it"
    start_time = time.time()

    try:
        response = requests.get(main_page_url, timeout=60)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        logging.info(f"Fetched main page successfully: {main_page_url}")

        # Extract Number of Articles
        num_articles = len(soup.find_all("a", class_="numero_articolo"))

        # Retrieve full-text URL
        button = soup.find("a", class_="float-right", target="blank", string=re.compile("visualizza atto intero", re.IGNORECASE))
        full_text_url = base_url + button["href"] if button and button.has_attr("href") else ""

        logging.info(f"Found {num_articles} articles and full-text URL: {full_text_url}")

        return num_articles, full_text_url

    except requests.RequestException as err:
        logging.error(f"Error fetching {main_page_url}: {err}")
        return 0, ""


def get_lavori_preparatori_html(main_page_url: str) -> str:
    """
    Fetches the HTML content of the 'lavori preparatori' page using Playwright.
    """
    base_url = "https://www.normattiva.it"
    start_time = time.time()

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(main_page_url, timeout=60000)
            logging.info(f"Loaded main page: {main_page_url}")

            # Find "lavori preparatori" link
            lavori_button = page.wait_for_selector("#lavori_preparatori_button", timeout=5000)
            if not lavori_button:
                logging.warning("Lavori preparatori button not found!")
                return ""

            data_href = lavori_button.get_attribute("data-href")
            if not data_href:
                logging.warning("No 'data-href' attribute found!")
                return ""

            lavori_url = base_url + data_href
            logging.info(f"Fetching data from: {lavori_url}")

            # Navigate to the lavori preparatori page
            page.goto(lavori_url, timeout=60000)
            page_content = page.content()

            logging.info(f"Finished fetching in {time.time() - start_time:.2f} seconds")
            return page_content

        except Exception as e:
            logging.error(f"Error fetching 'lavori preparatori' page: {e}")
            return ""
        finally:
            browser.close()


def sanitize_text(text: str) -> str:
    """
    Cleans text by removing newlines, tabs, excessive spaces.
    """
    if not isinstance(text, str):
        return text  # Return as is if not a string
    text = re.sub(r"\s+", " ", text.replace("\n", " ").replace("\t", " "))  # Remove newlines, tabs, extra spaces
    return text.strip()  # Trim spaces


def extract_lavori_preparatori(html_content: str):
    """
    Extracts:
    - Title
    - Publication date (in ISO 8601 format)
    - Brief description
    - Full 'Lavori Preparatori' content (including Senato and Camera)
    """
    start_time = time.time()
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract Title
    title_tag = soup.find("div", style="font-weight: bold;")
    title = sanitize_text(title_tag.get_text(strip=True)) if title_tag else ""

    # Transform title format
    match = re.search(r"LEGGE\s+\d+\s+\w+\s+(\d{4}),\s+n\.?\s*(\d+)", title, re.IGNORECASE)
    if match:
        title = sanitize_text(f"L. {match.group(2)}/{match.group(1)}")

    # Extract Date
    date_tag = soup.find("span", class_="riferimento")
    date_text = date_tag.get_text(strip=True) if date_tag else "N/A"

    # Extract date using regex and convert to ISO format
    date_match = re.search(r"(\d{1,2})-(\d{1,2})-(\d{4})", date_text)
    if date_match:
        day, month, year = date_match.groups()  # Extract day, month, year
        date = np.datetime64(f"{year}-{int(month):02d}-{int(day):02d}")  # Convert to YYYY-MM-DD
    else:
        date = np.datetime64("NaT")  # Handle missing date

    # Extract Brief Description
    description = "N/A"
    if title_tag:
        sibling_tag = title_tag.find_next_sibling(string=True)
        if sibling_tag:
            description = sanitize_text(str(sibling_tag).strip())

    # Extract LAVORI PREPARATORI (Full Content)
    pre_tag = soup.find("pre", class_="inline")
    lavori_preparatori = sanitize_text(pre_tag.get_text("\n", strip=True)) if pre_tag else "N/A"

    logging.info(f"Finished extraction in {time.time() - start_time:.2f} seconds")

    return [title, date, description, lavori_preparatori]


def extract_normattiva_data(url: str, csv_file_path="normattiva_db.csv"):
    """
    Extracts data from the main page and 'lavori preparatori' page and saves it to a CSV file.
    """
    num_articles, full_text_url = get_main_page_info(url)
    html = get_lavori_preparatori_html(url)
    extracted_data = extract_lavori_preparatori(html)

    # Create DataFrame
    df = pd.DataFrame(
        [extracted_data + [num_articles, full_text_url]],
        columns=["titolo", "data", "descrizione", "lavori_preparatori", "num_articoli", "full_text_url"],
    )
    logging.info(df)

    # Check if CSV file exists to avoid duplicate headers
    header_needed = not os.path.exists(csv_file_path)
    df.to_csv(csv_file_path, mode="a", index=False, header=header_needed, encoding="utf-16", quoting=csv.QUOTE_ALL)


if __name__ == "__main__":
    extract_normattiva_data(url="https://www.normattiva.it/atto/caricaDettaglioAtto?atto.dataPubblicazioneGazzetta=2025-01-24&atto.codiceRedazionale=25G00008&atto.articolo.numero=0&atto.articolo.sottoArticolo=1&atto.articolo.sottoArticolo1=0&qId=&tabID=0.1480355393949626&title=lbl.dettaglioAtto")
