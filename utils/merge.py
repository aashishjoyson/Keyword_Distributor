import pandas as pd
import os

def merge_amazon_files(uploaded_files):
    all_dfs = []
    for file in uploaded_files:
        df = pd.read_csv(file)
        all_dfs.append(df)

    merged_df = pd.concat(all_dfs, ignore_index=True)
    merged_df.to_csv(os.path.join("merged", "amazon_merged.csv"), index=False)
    return len(merged_df)

def merge_ebay_files(uploaded_files):
    all_dfs = []
    for file in uploaded_files:
        df = pd.read_csv(file)
        all_dfs.append(df)

    merged_df = pd.concat(all_dfs, ignore_index=True)
    merged_df.to_csv(os.path.join("merged", "ebay_merged.csv"), index=False)
    return len(merged_df)
