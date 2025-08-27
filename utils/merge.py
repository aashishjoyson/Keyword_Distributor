import pandas as pd
import os
from pathlib import Path

# Recognized platforms (lowercase substrings to match in filenames)
PLATFORM_KEYS = ["amazon_us", "amazon_uk", "amazon_de", "amazon_ca", "amazon_au", "ebay"]

def normalize_name(name: str) -> str:
    base = Path(name).stem.lower().strip().replace(" ", "_").replace("-", "_")
    return base

def match_platform(filename_stem: str) -> str | None:
    for key in PLATFORM_KEYS:
        if key in filename_stem:
            return key
    return None

def merge_uploaded_files(uploaded_files):
    """
    Accepts multiple uploaded CSV files (any subset of supported platforms).
    - Detects platform from filename (case-insensitive).
    - Merges multiple files per platform.
    - Writes merged CSVs to merged/{platform}.csv
    Returns dict: {platform: row_count} for platforms that were merged.
    """
    os.makedirs("merged", exist_ok=True)

    bucket = {k: [] for k in PLATFORM_KEYS}

    for up in uploaded_files:
        stem = normalize_name(up.name)
        platform = match_platform(stem)
        if not platform:
            # skip unknown
            continue
        df = pd.read_csv(up)
        bucket[platform].append(df)

    merged_counts = {}
    for platform, dfs in bucket.items():
        out_path = Path("merged") / f"{platform}.csv"
        if dfs:
            merged_df = pd.concat(dfs, ignore_index=True)
            merged_df.to_csv(out_path, index=False)
            merged_counts[platform] = len(merged_df)
        else:
            # If no upload for this platform in this run, do not touch existing files.
            pass

    return merged_counts
