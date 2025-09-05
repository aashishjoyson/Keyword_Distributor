# utils/generator.py
import requests
import time
import pandas as pd
from typing import Optional, Tuple, List, Dict

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "meta-llama/llama-4-maverick-17b-128e-instruct"

# Dropdown options -> output filenames your distributor expects
DOMAIN_OPTIONS = {
    "Amazon US (amazon.com)": "amazon_us.csv",
    "eBay (ebay.com)": "ebay.csv",
    "Amazon DE (amazon.de)": "amazon_de.csv",
    "Amazon UK (amazon.co.uk)": "amazon_uk.csv",
    "Amazon CA (amazon.ca)": "amazon_ca.csv",
    "Amazon AU (amazon.com.au)": "amazon_au.csv",
}

def _norm(s: str) -> str:
    """Normalize column names for fuzzy matching."""
    return "".join(s.strip().lower().replace("_", " ").split())

def detect_columns(columns: List[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Find product title, link, and keywords columns with case/space-insensitive matching.
    Returns (title_col, link_col, keywords_col) – any can be None if not found.
    """
    title_candidates = {"producttitle", "producttitles", "title"}
    link_candidates = {"link", "links", "url", "urls", "producturl", "productlink"}
    keyword_candidates = {"keyword", "keywords", "searchterm", "searchterms"}

    title_col = link_col = keywords_col = None
    for c in columns:
        n = _norm(c)
        if not title_col and n in title_candidates:
            title_col = c
        if not link_col and n in link_candidates:
            link_col = c
        if not keywords_col and n in keyword_candidates:
            keywords_col = c
    return title_col, link_col, keywords_col

def _generate_keyword_one(title: str, api_key: str, retries: int = 3, delay: float = 1.5) -> str:
    """Call Groq API to get a concise two-word search term."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You generate concise, high-quality two-word search terms."},
            {"role": "user",
             "content": (
                 "Generate one high-quality two-word generic search term for this product title: "
                 f"'{title}'. Do not use brand names, numbers, or sizes. Output only the two words."
             )},
        ],
        "temperature": 0.3,
        "max_tokens": 20,
    }
    for attempt in range(retries):
        try:
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
            if resp.status_code == 429:
                time.sleep(delay * (attempt + 1))
                continue
            resp.raise_for_status()
            data = resp.json()
            kw = data["choices"][0]["message"]["content"].strip()
            return kw
        except Exception as e:
            if attempt == retries - 1:
                return f"ERROR: {e}"
            time.sleep(delay * (attempt + 1))
    return "ERROR: Max retries exceeded"

def generate_keywords_for_df(
    df: pd.DataFrame,
    api_key: str,
    title_col: Optional[str],
    link_col: Optional[str],
    keywords_col: Optional[str],
    progress_cb=None,
    delay_seconds: float = 1.5,
    retries: int = 3,
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Generate keywords row-by-row. If keywords column missing, create it.
    - Skips rows where keywords already exist/non-empty.
    - Returns final_df (Keywords[, Links]) and stats dict.
    """
    # Ensure keywords column exists
    if not keywords_col:
        keywords_col = "Keywords"
        if "Keywords" not in df.columns:
            df["Keywords"] = ""
    # Make it string type to avoid dtype issues
    df[keywords_col] = df[keywords_col].astype("object")

    total = len(df)
    generated = failed = skipped = 0

    for i in range(total):
        title = str(df.at[i, title_col]) if title_col in df.columns else ""
        existing = str(df.at[i, keywords_col]) if keywords_col in df.columns else ""
        if title and (existing.strip() == "" or existing.strip().lower().startswith("error")):
            kw = _generate_keyword_one(title, api_key=api_key, retries=retries, delay=delay_seconds)
            df.at[i, keywords_col] = kw
            if kw.startswith("ERROR"):
                failed += 1
            else:
                generated += 1
            time.sleep(delay_seconds)  # gentle rate limiting
        else:
            skipped += 1
        if progress_cb:
            progress_cb(i + 1, total)

    # Build final distributor-ready frame
    cols = []
    # Put Keywords first
    cols.append(keywords_col)
    # Then Links if present
    if link_col and link_col in df.columns:
        cols.append(link_col)

    final_df = df[cols].copy()
    # Standardize column names: Keywords[, Links]
    final_df.rename(columns={keywords_col: "Keywords"}, inplace=True)
    if link_col and link_col in final_df.columns:
        final_df.rename(columns={link_col: "Links"}, inplace=True)

    stats = {"generated": generated, "failed": failed, "skipped": skipped}
    return final_df, stats

