import pandas as pd
import os
from pathlib import Path
import zipfile
import shutil
from datetime import timedelta
from calendar import monthrange
import streamlit as st
import matplotlib.pyplot as plt

def distribute_keywords(start_date):
    amazon_path = "merged/amazon_merged.csv"
    ebay_path   = "merged/ebay_merged.csv"

    if not os.path.exists(amazon_path) or not os.path.exists(ebay_path):
        return False

    amazon_df = pd.read_csv(amazon_path)
    ebay_df   = pd.read_csv(ebay_path)

    amazon_total = len(amazon_df)
    ebay_total   = len(ebay_df)

    # Full days possible by data
    days_am = amazon_total // 1000
    days_eb = ebay_total   // 1000
    days_data = min(days_am, days_eb)

    # Days left in month
    tot_days = monthrange(start_date.year, start_date.month)[1]
    rem_days = tot_days - start_date.day + 1

    days_to_dist = min(days_data, rem_days)

    ptr_am = ptr_eb = 0

    base = Path("distributed") / f"{start_date.strftime('%Y-%m')}_distribution"
    base.mkdir(parents=True, exist_ok=True)

    for offset in range(days_to_dist):
        curr = start_date + timedelta(days=offset)
        day_str = curr.strftime("%Y-%m-%d")
        day_folder = base / day_str
        day_folder.mkdir(exist_ok=True, parents=True)

        for acct in range(1, 21):
            acct_folder = day_folder / f"account_{acct}"
            acct_folder.mkdir(exist_ok=True, parents=True)

            am_chunk = amazon_df.iloc[ptr_am:ptr_am+50]
            eb_chunk = ebay_df.iloc[ptr_eb:ptr_eb+50]
            ptr_am += 50
            ptr_eb += 50

            am_chunk.to_csv(acct_folder / f"amazon_us_{curr.strftime('%m-%d')}.csv", index=False)
            eb_chunk.to_csv(acct_folder / f"ebay_{curr.strftime('%m-%d')}.csv", index=False)

    # Create one monthly ZIP
    zip_path = f"distributed/{start_date.strftime('%Y-%m')}_distribution.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for root, _, files in os.walk(base):
            for f in files:
                p = os.path.join(root, f)
                zf.write(p, os.path.relpath(p, start=base.parent))

    # Clean up unzipped folders
    shutil.rmtree(base)

    # Leftovers
    rem_am_df = amazon_df.iloc[ptr_am:]
    rem_eb_df = ebay_df.iloc[ptr_eb:]
    os.makedirs("leftover", exist_ok=True)
    am_path = eb_path = None

    if not rem_am_df.empty:
        am_path = "leftover/undistributed_amazon.csv"
        rem_am_df.to_csv(am_path, index=False)
    if not rem_eb_df.empty:
        eb_path = "leftover/undistributed_ebay.csv"
        rem_eb_df.to_csv(eb_path, index=False)

    # Visualization
    st.subheader("📊 Distribution Summary")
    st.write(f"Total Amazon rows: {amazon_total}")
    st.write(f"Total eBay rows:   {ebay_total}")
    st.write(f"Days distributed:  {days_to_dist}")
    st.write(f"Leftover Amazon:   {amazon_total - ptr_am}")
    st.write(f"Leftover eBay:     {ebay_total   - ptr_eb}")

    labels = ["Distributed","Leftover"]
    fig, axes = plt.subplots(1,2,figsize=(10,4))
    axes[0].pie([ptr_am, amazon_total-ptr_am], labels=labels, autopct='%1.1f%%', startangle=90)
    axes[0].set_title("Amazon")
    axes[1].pie([ptr_eb, ebay_total-ptr_eb], labels=labels, autopct='%1.1f%%', startangle=90)
    axes[1].set_title("eBay")
    st.pyplot(fig)

    return {
        "days_distributed": days_to_dist,
        "zip_path": zip_path,
        "amazon_download": am_path,
        "ebay_download": eb_path
    }
