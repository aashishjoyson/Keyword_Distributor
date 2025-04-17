import pandas as pd
import os

def merge_amazon_files(uploaded_files):
    all_dfs = []
    for file in uploaded_files:
        df = pd.read_csv(file)
        all_dfs.append(df)

    # Clear any pre-existing merged files to avoid issues from previous sessions
    merged_path = os.path.join("merged", "amazon_merged.csv")
    if os.path.exists(merged_path):
        os.remove(merged_path)

    # Merge the uploaded Amazon files
    merged_df = pd.concat(all_dfs, ignore_index=True)
    merged_df.to_csv(merged_path, index=False)
    return len(merged_df)

def merge_ebay_files(uploaded_files):
    all_dfs = []
    for file in uploaded_files:
        df = pd.read_csv(file)
        all_dfs.append(df)

    # Clear any pre-existing merged files to avoid issues from previous sessions
    merged_path = os.path.join("merged", "ebay_merged.csv")
    if os.path.exists(merged_path):
        os.remove(merged_path)

    # Merge the uploaded eBay files
    merged_df = pd.concat(all_dfs, ignore_index=True)
    merged_df.to_csv(merged_path, index=False)
    return len(merged_df)
