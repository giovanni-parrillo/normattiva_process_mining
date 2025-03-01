import logging
import json
from pydantic import BaseModel
from typing import Optional
import pandas as pd
from ollama import chat
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClassificationResult(BaseModel):
    category: Optional[str]

# The final list of categories:
CATEGORIES = [
    "Agricoltura, caccia e pesca",
    "Difesa e forze armate",
    "Sicurezza pubblica e gestione emergenze",
    "Istruzione, cultura, informazione e religione",
    "Diritti, giustizia e minoranze",
    "Economia, finanza e commercio",
    "Istituzioni, governo e politica",
    "Affari esteri",
    "Ambiente e risorse naturali",
    "Politiche abitative e sviluppo urbano",
    "Trasporti e infrastrutture",
    "Sanità e salute pubblica",
    "Lavoro e affari sociali",
    "Energia",
    "Turismo"
]



def classify_law_description(desc: str) -> Optional[str]:
    """
    Uses Ollama to classify a given 'descrizione' into exactly one of the categories in CATEGORIES.
    Returns the category name, or None if classification fails.
    """
    system_prompt = (
        "You are a text classification assistant. "
        "I will provide you with a list of possible categories, and a short text. "
        "You must pick exactly ONE category that best fits the text. "
        "If uncertain, pick the closest match. "
        "Do NOT provide additional commentary, only the chosen category."
    )

    # Summarize categories in the user prompt or system prompt:
    categories_str = "\n".join(f"- {cat}" for cat in CATEGORIES)

    user_prompt = (
        f"Categories:\n{categories_str}\n\n"
        f"Text:\n{desc}\n\n"
        f"Output only the exact category string from the list above."
    )

    # We'll do a simple text-only approach (no special JSON schema).
    logger.info("Classifying text with the LLM...")

    response = chat(
        model="llama3.2:1B",  # or whichever model you have
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # Optionally we can keep format=None or omit it entirely
        # because we want just raw text (the final category).
        format=None,
        options={'temperature': 0.1},  
        stream=False
    )

    # Check the returned structure
    if hasattr(response, "message") and hasattr(response.message, "content") and response.message.content:
        output_text = response.message.content.strip()
    else:
        output_text = (response.get("content") or "").strip()

    logger.info("Raw classification output: %s", output_text)

    # We can do a final check: if the output is exactly one of our known categories, accept it
    if output_text in CATEGORIES:
        return output_text
    else:
        # You might want to do some fuzzy matching or fallback
        # For now, just return None if the model didn't comply
        logger.warning("Model output not in known categories.")
        return None


def main():
    # Suppose we have a CSV with columns: ["id", "descrizione"]
    df = pd.read_csv("normattiva.csv")
    df = df.sample(n=1)

    pattern = r'\b(?:conversione|legge|decreto|decreto\-legge|ratifica|Disposizione)\b'
    df["descrizione"] = df["descrizione"].apply(lambda x: re.sub(pattern, "", x, flags=re.IGNORECASE))

    # We'll store the classification results in a new column
    categories_out = []
    for idx, row in df.iterrows():
        desc = row["descrizione"]
        cat = classify_law_description(desc)
        categories_out.append(cat)

    df["category"] = categories_out

    # Print out the description and its category
    for idx, row in df.iterrows():
        print("Descrizione:", row["descrizione"])
        print("Category:", row["category"])
        print("-" * 40)


if __name__ == "__main__":
    main()
