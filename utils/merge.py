import pandas as pd
import os

def save_uploaded_file(uploaded_file, save_path):
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

def merge_uploaded_files(uploaded_files):
    """
    Processes and merges uploaded files by platform based on their names.
    Returns a dictionary with row counts per platform.
    """
    merged_counts = {}
    os.makedirs("merged", exist_ok=True)

    platforms = {
        "amazon_us": [],
        "ebay": [],
        "amazon_de": [],
        "amazon_uk": [],
        "amazon_ca": [],
        "amazon_au": []
    }

    for file in uploaded_files:
        file_name = file.name.lower().replace(".csv", "")
        for platform in platforms.keys():
            if platform in file_name:
                df = pd.read_csv(file)
                platforms[platform].append(df)
                break

    for platform, dfs in platforms.items():
        if dfs:
            merged_df = pd.concat(dfs, ignore_index=True)
            merged_df.to_csv(f"merged/{platform}.csv", index=False)
            merged_counts[platform] = len(merged_df)

    return merged_counts
