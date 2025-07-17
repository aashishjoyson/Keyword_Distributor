import pandas as pd
import os

PLATFORM_KEYS = ["amazon_us", "ebay", "amazon_de", "amazon_uk", "amazon_ca", "amazon_au"]

def process_uploaded_files(uploaded_files):
    os.makedirs("merged", exist_ok=True)
    row_counts = {}
    saved_paths = {}
    total_files = 0

    for file in uploaded_files:
        filename = file.name.lower().replace(".csv", "").strip()
        matched_platform = next((key for key in PLATFORM_KEYS if key in filename), None)

        if matched_platform:
            df = pd.read_csv(file)
            total_files += 1

            merged_path = os.path.join("merged", f"{matched_platform}.csv")
            if os.path.exists(merged_path):
                existing_df = pd.read_csv(merged_path)
                df = pd.concat([existing_df, df], ignore_index=True)

            df.to_csv(merged_path, index=False)
            row_counts[matched_platform] = len(df)
            saved_paths[matched_platform] = merged_path

    return {
        "total_files": total_files,
        "row_counts": row_counts,
        "saved_paths": saved_paths
    }
