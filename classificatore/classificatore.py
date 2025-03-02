import logging
import json
from pydantic import BaseModel
from typing import Optional, Tuple, Dict, Union
import pandas as pd
from ollama import chat
import re
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ClassificationResult(BaseModel):
    first_category: Optional[str]
    first_confidence: Optional[float]
    second_category: Optional[str]
    second_confidence: Optional[float]
    # third_category: Optional[str]
    # third_confidence: Optional[float]

# The final list of categories:
CATEGORIES = [
    "Agricoltura, caccia e pesca",
    "Difesa e forze armate",
    "Sicurezza e gestione emergenze",
    "Istruzione, cultura, informazione e religione",
    "Diritti civili e politici",
    "Giustizia e diritto",
    "Tassazione e spesa pubblica",
    "Economia, finanza e commercio",
    "Istituzioni, governo e politica",
    "Affari intrnazionali e cooperazione",
    "Regioni ed enti locali",
    "Unione Europea",
    "Ambiente e risorse naturali",
    "Politiche abitative e sviluppo urbano",
    "Trasporti e infrastrutture",
    "Sanità e salute pubblica",
    "Lavoro, Welfare e affari sociali",
    "Tecnologia, ricerca e innovazione",
    "Incerto"
]

def classify_law_description(desc: str) -> Dict[str, Optional[Union[str, float]]]:
    """
    Uses Ollama to classify a given 'descrizione' into exactly two categories from CATEGORIES.
    Returns a dictionary containing first and second choice with confidence levels.
    """
    system_prompt = (
        "Sei un assistente di classificazione del testo altamente accurato. "
        "Riceverai un breve testo e una lista di categorie predefinite. "
        "Il tuo compito è selezionare ESATTAMENTE DUE categorie, ordinandole per rilevanza, "
        "con la prima scelta la più appropriata e la seconda la successiva. "
        "Per ciascuna fornisci una probabilità di confidenza (compresa tra 0 e 1). "
        "Se sei incerto, scegli 'Incerto'. "
        "Rispondi SOLO in formato JSON nel seguente schema: "
        "{ \"first_category\": \"Categoria\", \"first_confidence\": 0.85, \"second_category\": \"Categoria\", \"second_confidence\": 0.45 }"
    )

    categories_str = "\n".join(f"- {cat}" for cat in CATEGORIES)

    user_prompt = (
        f"Categories:\n{categories_str}\n\n"
        f"Text:\n{desc}\n\n"
        f"Output ONLY in JSON format."
    )

    logger.info("Classifying text with the LLM...")

    response = chat(
        model="deepseek-r1:14b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={'temperature': 0},
        format="json",
        stream=False
    )

    # Extract the model response
    if hasattr(response, "message") and response.message.content is not None:
        output_text = response.message.content.strip()
    elif response.get("content") is not None:
        output_text = response.get("content").strip()
    else:
        output_text = ""
    # logger.info("Raw output: %s", output_text)

    # Attempt to parse JSON output
    try:
        classification_data = json.loads(output_text)

        first_category = classification_data.get("first_category", "Incerto")
        first_confidence = classification_data.get("first_confidence", 0.0)
        second_category = classification_data.get("second_category", "Incerto")
        second_confidence = classification_data.get("second_confidence", 0.0)
        # third_category = classification_data.get("third_category", "Incerto")
        # third_confidence = classification_data.get("third_confidence", 0.0)

        # Validate categories
        if first_category not in CATEGORIES:
            logger.warning("First category not in known categories. Setting to 'Incerto'.")
            first_category = "Incerto"
            first_confidence = 0.0

        if second_category not in CATEGORIES:
            logger.warning("Second category not in known categories. Setting to 'Incerto'.")
            second_category = "Incerto"
            second_confidence = 0.0

        # if third_category not in CATEGORIES:
        #     logger.warning("Third category not in known categories. Setting to 'Incerto'.")
        #     third_category = "Incerto"
        #     third_confidence = 0.0

        return {
            "first_category": first_category,
            "first_confidence": first_confidence,
            "second_category": second_category,
            "second_confidence": second_confidence,
            # "third_category": third_category,
            # "third_confidence": third_confidence
        }

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON from model output.")
        return {
            "first_category": "Incerto",
            "first_confidence": 0.0,
            "second_category": "Incerto",
            "second_confidence": 0.0,
            # "third_category": "Incerto",
            # "third_confidence": 0.0
        }

def main():
    df = pd.read_csv("normattiva.csv")
    df = df.dropna(subset=["descrizione"])
    df = df[df["descrizione"].astype(str).str.strip() != ""]

    # Apply pre-processing: Remove generic legal terms
    pattern = r'\b(?:conversione|legge|decreto|decreto-legge|ratifica|Disposizione|convenzione|proroga|modifiche|concessione|esercizio|modificazione|delega|governo|adesione|autorizzazione|approvazione|disposizioni|norme|esecuzione|provvedimento|estensione|regolamento|provvedimenti|comma|statuto|protocollo|Presidente|Repubblica|modifica|modificazioni|convertito|regio|legislativo|articolo|articoli|emanato|ai sensi|recante|concernente|urgenti|n.|urgente|concernenti|decreti|legislativi|abrogazione|istitutiva|art.|presidenza|interpretazione|autentica|commi)\b'

    df["descrizione"] = df["descrizione"].apply(lambda x: re.sub(pattern, "", str(x), flags=re.IGNORECASE) if isinstance(x, str) else x)

    # Apply pre-processing: Remove numbers, months, and extra spaces
    df["descrizione"] = df["descrizione"].apply(lambda x: re.sub(r"[0-9,\.]", "", str(x)) if isinstance(x, str) else "")
    months_pattern = r'\b(?:gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\b'
    df["descrizione"] = df["descrizione"].apply(lambda x: re.sub(months_pattern, "", x, flags=re.IGNORECASE) if isinstance(x, str) else x)
    df["descrizione"] = df["descrizione"].apply(lambda x: re.sub(r" (?:-|n) ", " ", str(x)) if isinstance(x, str) else x)
    df["descrizione"] = df["descrizione"].apply(lambda x: re.sub(pattern, "", str(x), flags=re.IGNORECASE) if isinstance(x, str) else "")
    df["descrizione"] = df["descrizione"].apply(lambda x: re.sub(r'\s{2,}', ' ', x).strip() if isinstance(x, str) else x)

    df_sample = df.sample(n=50)

    classification_results = []

    for idx, row in df_sample.iterrows():
        desc = row["descrizione"]
        titolo = row["titolo"]
        classification = {"titolo": titolo, "descrizione": desc}
        classification.update(classify_law_description(desc))
        classification_results.append(classification)

        # Append this classification result to the CSV after each iteration.
        df_row = pd.DataFrame([classification])
        csv_file = "classificatore/classification_results.csv"
        if os.path.exists(csv_file):
            df_row.to_csv(csv_file, mode='a', index=False, encoding="utf-8", header=False)
        else:
            df_row.to_csv(csv_file, index=False, encoding="utf-8")

    # Convert all classification results to JSON format and print
    output_json = json.dumps(classification_results, indent=4, ensure_ascii=False)
    print(output_json)

if __name__ == "__main__":
    main()
