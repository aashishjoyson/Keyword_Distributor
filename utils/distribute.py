import pandas as pd
import os
from pathlib import Path
import zipfile
import shutil
from datetime import timedelta
from calendar import monthrange

# Discover available platform CSVs in /merged dynamically
def _discover_platforms(merged_folder: str) -> list[str]:
    p = Path(merged_folder)
    if not p.exists():
        return []
    return sorted([f.stem for f in p.glob("*.csv")])

def distribute_keywords(start_date, accounts: int = 23, rows_per_account: int = 100):
    """
    Distribute only the platforms that exist in merged/.
    - accounts: number of accounts per day (user-chosen)
    - rows_per_account: rows per account (fixed at 100 as per requirement)
    Returns a dict with distribution results and paths.
    """
    merged_folder = "merged"
    distributed_folder = "distributed"
    leftover_folder = "leftover"
    os.makedirs(distributed_folder, exist_ok=True)
    os.makedirs(leftover_folder, exist_ok=True)

    platforms = _discover_platforms(merged_folder)
    if not platforms:
        return False

    # Load only the available platforms
    platform_dfs = {}
    total_rows = {}
    pointers = {}
    for platform in platforms:
        path = os.path.join(merged_folder, f"{platform}.csv")
        if not os.path.exists(path):
            # Shouldn't happen due to discovery, but safe-guard
            continue
        df = pd.read_csv(path)
        platform_dfs[platform] = df
        total_rows[platform] = len(df)
        pointers[platform] = 0

    if not platform_dfs:
        return False

    rows_per_day = accounts * rows_per_account

    # How many full days can we distribute across ALL included platforms?
    # (min across platforms so each day's folder has all included platforms)
    def days_possible_for(n_rows: int) -> int:
        return n_rows // rows_per_day

    days_possible = min(days_possible_for(total_rows[p]) for p in platform_dfs.keys())
    # Fit within the remaining days in the month from start_date
    total_days_in_month = monthrange(start_date.year, start_date.month)[1]
    remaining_days = total_days_in_month - start_date.day + 1
    days_to_distribute = min(days_possible, remaining_days)

    daily_distribution = []

    # Base folder (unzipped)
    base = Path(distributed_folder) / f"{start_date.strftime('%Y-%m')}_distribution"
    base.mkdir(parents=True, exist_ok=True)

    # Distribute day by day
    for offset in range(days_to_distribute):
        curr_date = start_date + timedelta(days=offset)
        day_folder = base / curr_date.strftime('%Y-%m-%d')
        day_folder.mkdir(parents=True, exist_ok=True)

        # Track daily counts per platform (for charts)
        summary = {"date": curr_date.strftime('%Y-%m-%d')}

        for acc in range(1, accounts + 1):
            acc_folder = day_folder / f"account_{acc}"
            acc_folder.mkdir(parents=True, exist_ok=True)
            for platform, df in platform_dfs.items():
                ptr = pointers[platform]
                # Slice for this account
                chunk = df.iloc[ptr:ptr + rows_per_account]
                pointers[platform] += len(chunk)  # in case last partial day ever occurs
                # Save file: {platform}_{MM-DD}.csv
                out_name = f"{platform}_{curr_date.strftime('%m-%d')}.csv"
                chunk.to_csv(acc_folder / out_name, index=False)

        # Daily counts per platform (how many rows written this day)
        for platform in platform_dfs.keys():
            start_ptr = max(0, pointers[platform] - rows_per_day)
            day_count = pointers[platform] - start_ptr
            summary[platform] = day_count

        daily_distribution.append(summary)

    # Zip the distribution folder
    zip_path = f"{distributed_folder}/{start_date.strftime('%Y-%m')}_distribution.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for root, _, files in os.walk(base):
            for fname in files:
                p = os.path.join(root, fname)
                zf.write(p, os.path.relpath(p, start=base.parent))

    # Remove the unzipped folder to keep only ZIP
    shutil.rmtree(base, ignore_errors=True)

    # Leftovers per platform
    leftover_paths = {}
    for platform, df in platform_dfs.items():
        ptr = pointers[platform]
        leftover_df = df.iloc[ptr:]
        leftover_path = None
        if not leftover_df.empty:
            leftover_path = os.path.join(leftover_folder, f"undistributed_{platform}.csv")
            leftover_df.to_csv(leftover_path, index=False)
        leftover_paths[platform] = leftover_path

    # Build result
    result = {
        "platforms": list(platform_dfs.keys()),
        "days_distributed": days_to_distribute,
        "zip_path": zip_path,
        "daily_distribution": daily_distribution,
        "accounts": accounts,
        "rows_per_account": rows_per_account,
    }

    for platform in platform_dfs.keys():
        result[f"{platform}_distributed"] = pointers[platform]
        result[f"remaining_{platform}"] = total_rows[platform] - pointers[platform]
        result[f"{platform}_download"] = leftover_paths[platform]

    return result
