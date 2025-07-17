import pandas as pd
import os

PLATFORM_KEYS = ["amazon_us", "ebay", "amazon_de", "amazon_uk", "amazon_ca", "amazon_au"]

def save_uploaded_file(uploaded_file, save_dir="merged"):
    os.makedirs(save_dir, exist_ok=True)
    # Normalize file name (handles cases like "Amazon_US.csv" or "amazon_us.csv")
    filename = uploaded_file.name.split(".")[0].strip().lower().replace(" ", "_").replace("-", "_") + ".csv"
    file_path = os.path.join(save_dir, filename)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    return file_path

def merge_uploaded_files(uploaded_files):
    all_dfs = {platform: [] for platform in PLATFORM_KEYS}

    for uploaded_file in uploaded_files:
        normalized_name = uploaded_file.name.split(".")[0].strip().lower().replace(" ", "_").replace("-", "_")
        if normalized_name not in PLATFORM_KEYS:
            continue
        df = pd.read_csv(uploaded_file)
        all_dfs[normalized_name].append(df)

    os.makedirs("merged", exist_ok=True)
    for platform, dfs in all_dfs.items():
        merged_path = os.path.join("merged", f"{platform}.csv")
        if dfs:
            merged_df = pd.concat(dfs, ignore_index=True)
            merged_df.to_csv(merged_path, index=False)

    merged_counts = {platform: len(pd.read_csv(os.path.join("merged", f"{platform}.csv"))) 
                     for platform in PLATFORM_KEYS if os.path.exists(os.path.join("merged", f"{platform}.csv")))}

    return merged_counts
