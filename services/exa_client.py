import os
import requests
from dotenv import load_dotenv

load_dotenv()

EXA_API_KEY = os.getenv("EXA_API_KEY")

EXA_SEARCH_URL = "https://api.exa.ai/search"
EXA_CONTENTS_URL = "https://api.exa.ai/contents"


def search_companies(query, num_results=8):
    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "query": query,
        "type": "auto",
        "numResults": num_results,
        "category": "company",
        "contents": {
            "highlights": {
                "maxCharacters": 500
            }
        }
    }

    response = requests.post(EXA_SEARCH_URL, json=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Exa search failed: {response.text}")

    data = response.json()

    results = []
    for r in data.get("results", []):
        highlights = r.get("highlights", [])
        text = " ".join(highlights) if highlights else ""

        results.append({
            "title": r.get("title"),
            "url": r.get("url"),
            "snippet": text
        })

    return results


def get_contents(urls):
    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "urls": urls,
        "text": True
    }

    response = requests.post(EXA_CONTENTS_URL, json=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Exa contents failed: {response.text}")

    data = response.json()

    contents = []
    for item in data.get("results", []):
        contents.append({
            "url": item.get("url"),
            "text": item.get("text", "")[:5000]
        })

    return contents