import pandas as pd
import os
from pathlib import Path
import zipfile
import shutil
from datetime import timedelta
from calendar import monthrange

PLATFORM_KEYS = ["amazon_us", "ebay", "amazon_de", "amazon_uk", "amazon_ca", "amazon_au"]

def distribute_keywords(start_date):
    merged_folder = "merged"
    distributed_folder = "distributed"
    leftover_folder = "leftover"
    os.makedirs(distributed_folder, exist_ok=True)
    os.makedirs(leftover_folder, exist_ok=True)

    platform_dfs = {}
    total_rows = {}
    pointers = {}

    for platform in PLATFORM_KEYS:
        path = os.path.join(merged_folder, f"{platform}.csv")
        if not os.path.exists(path):
            return False
        df = pd.read_csv(path)
        platform_dfs[platform] = df
        total_rows[platform] = len(df)
        pointers[platform] = 0

    # Calculate number of full days possible
    days_possible = min(len(df) // (23 * 100) for df in platform_dfs.values())

    # Calculate days left in month
    total_days_in_month = monthrange(start_date.year, start_date.month)[1]
    remaining_days = total_days_in_month - start_date.day + 1
    days_to_distribute = min(days_possible, remaining_days)

    daily_distribution = []

    base = Path(distributed_folder) / f"{start_date.strftime('%Y-%m')}_distribution"
    base.mkdir(parents=True, exist_ok=True)

    for offset in range(days_to_distribute):
        current_date = start_date + timedelta(days=offset)
        date_folder = base / current_date.strftime('%Y-%m-%d')
        date_folder.mkdir(parents=True, exist_ok=True)

        distribution_summary = {"date": current_date.strftime('%Y-%m-%d')}

        for account in range(1, 24):
            account_folder = date_folder / f"account_{account}"
            account_folder.mkdir(parents=True, exist_ok=True)

            for platform in PLATFORM_KEYS:
                df = platform_dfs[platform]
                ptr = pointers[platform]
                chunk = df.iloc[ptr:ptr + 100]
                pointers[platform] += 100

                chunk.to_csv(account_folder / f"{platform}_{current_date.strftime('%m-%d')}.csv", index=False)

        for platform in PLATFORM_KEYS:
            distributed_count = min((offset + 1) * 23 * 100, total_rows[platform])
            distribution_summary[platform] = distributed_count

        daily_distribution.append(distribution_summary)

    # Zip the distribution folder
    zip_path = f"{distributed_folder}/{start_date.strftime('%Y-%m')}_distribution.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for root, _, files in os.walk(base):
            for file in files:
                full_path = os.path.join(root, file)
                zf.write(full_path, os.path.relpath(full_path, base.parent))

    shutil.rmtree(base)

    # Save leftover files
    leftover_paths = {}
    for platform in PLATFORM_KEYS:
        df = platform_dfs[platform]
        ptr = pointers[platform]
        leftover_df = df.iloc[ptr:]
        leftover_path = None
        if not leftover_df.empty:
            leftover_path = os.path.join(leftover_folder, f"undistributed_{platform}.csv")
            leftover_df.to_csv(leftover_path, index=False)
        leftover_paths[platform] = leftover_path

    result = {
        "days_distributed": days_to_distribute,
        "zip_path": zip_path,
        "daily_distribution": daily_distribution
    }

    for platform in PLATFORM_KEYS:
        result[f"{platform}_distributed"] = pointers[platform]
        result[f"remaining_{platform}"] = total_rows[platform] - pointers[platform]
        result[f"{platform}_download"] = leftover_paths[platform]

    return result
