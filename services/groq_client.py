import ast
import os
import json
from groq import Groq
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator
from typing import List
from utils.prompts import build_analysis_prompt
from utils.post_process import post_process

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class CompanyAnalysis(BaseModel):
    name: str
    summary: str
    target_audience: str
    features: List[str]
    pricing: str
    confidence: int
    sources: List[str]

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v):
        v = float(v)
        if v <= 1.0:
            return int(v * 100)
        return int(v)

    @field_validator("features", mode="before")
    @classmethod
    def cap_features(cls, v):
        if isinstance(v, dict):
            v = list(v.values())
        items = [str(i) for i in v]
        return items[:5]


def call_llm(messages, model="llama-3.1-8b-instant", json_mode=False):
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def filter_companies(results):
    content = "\n\n".join([
        f"{i+1}. {r['title']} - {r['snippet']}"
        for i, r in enumerate(results)
    ])

    prompt = f"""
You are a strict analyst.

From the list below, return ONLY real companies or products (not blogs, news, directories).

List:
{content}

Return output as a Python list of indices (1-based), max 5.
Example: [1, 3, 5]
"""

    response = call_llm([
        {"role": "user", "content": prompt}
    ])

    try:
        indices = ast.literal_eval(response)
        return [results[i-1] for i in indices if 0 < i <= len(results)]
    except:
        return results[:3]


def analyze_company(content, url):
    prompt = build_analysis_prompt(content, url)
    response = call_llm([{"role": "user", "content": prompt}], json_mode=True)
    try:
        raw = json.loads(response)
        validated = CompanyAnalysis(**raw).model_dump()
        return post_process(validated, url, content)
    except Exception as e:
        print(f"[analyze_company] Failed for {url}: {e}")
        return None