import os
import json
from pathlib import Path
from typing import Optional, Tuple
from openai import OpenAI

CONFIG = json.loads((Path(__file__).parent.parent / "config.json").read_text())

# Initialize OpenAI client using OPENAI_API_KEY and optional OPENAI_BASE_URL
client_kwargs = {}
if os.getenv("OPENAI_BASE_URL"):
    client_kwargs["base_url"] = os.getenv("OPENAI_BASE_URL")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    **client_kwargs
)

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def detect_product(text: str) -> Optional[str]:
    """Return 'Solvea', 'VOC.ai', or None based on keyword match."""
    text_lower = text.lower()
    scores = {}
    for product, data in CONFIG["products"].items():
        score = sum(1 for kw in data["trigger_keywords"] if kw in text_lower)
        if score > 0:
            scores[product] = score
    if not scores:
        return None
    return max(scores, key=scores.get)


def generate_reply(post_title: str, post_content: str, platform: str) -> Tuple[Optional[str], Optional[str]]:
    """Generates a contextual reply using OpenAI."""
    product = detect_product(f"{post_title} {post_content}")
    if not product:
        return None, None

    prod_config = CONFIG["products"][product]

    prompt = f"""You are a helpful user sharing your genuine experience on {platform}.

Product info:
- Name: {prod_config['name']}
- Pitch: {prod_config['pitch']}

Post Title: {post_title}
Post Content: {post_content}

Write a natural, helpful reply recommending {prod_config['name']} naturally.
Keep it concise (2-4 sentences), non-salesy, and relevant. Do not include quotes around the response.
"""

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=250,
    )

    reply_text = response.choices[0].message.content.strip()
    return reply_text, product


def evaluate_relevance(post_title: str, post_content: str) -> bool:
    """Evaluates whether a post is relevant using OpenAI."""
    prompt = f"""Evaluate if this post is relevant for a product recommendation.

Post Title: {post_title}
Post Content: {post_content}

Reply strictly with YES or NO.
"""

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=10,
    )

    answer = response.choices[0].message.content.strip().upper()
    return "YES" in answer


def analyze_lead(post_title: str, post_content: str) -> dict:
    """Analyzes a lead using OpenAI."""
    prompt = f"""Analyze this post for lead generation context:

Post Title: {post_title}
Post Content: {post_content}

Return JSON with keys: 'intent' (str), 'urgency' ('high'/'medium'/'low'), 'competitor_mentioned' (bool).
"""

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=150,
    )

    try:
        return json.loads(response.choices[0].message.content.strip())
    except Exception:
        return {"intent": "unknown", "urgency": "low", "competitor_mentioned": False}
