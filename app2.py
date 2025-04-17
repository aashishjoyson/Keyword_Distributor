import streamlit as st
from utils.merge import merge_amazon_files, merge_ebay_files
from utils.distribute import distribute_keywords

import os
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Keyword Distributor", layout="wide")
st.title("📦 Keyword Distributor")

st.markdown("""
Welcome to **Keyword Distributor**! 🚀

- Merge multiple Amazon & eBay keyword CSVs
- Visualize merge counts
- Distribute into 20‑account daily batches
- Download a single monthly ZIP of all distributions
- Download leftover keywords
""")

st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Merge Files", "Distribute Keywords"])

# Ensure necessary folders exist
for folder in ["uploads", "merged", "distributed", "leftover"]:
    os.makedirs(folder, exist_ok=True)

if page == "Merge Files":
    st.header("🛠️ Merge Amazon & eBay Files")
    st.write("Upload CSVs (columns: `Keyword`,`Link`).")

    amazon_files = st.file_uploader("Amazon CSVs", accept_multiple_files=True, key="amazon")
    ebay_files   = st.file_uploader("eBay CSVs", accept_multiple_files=True, key="ebay")

    if st.button("Merge Files"):
        merged = False

        if amazon_files:
            amazon_rows = merge_amazon_files(amazon_files)
            st.success(f"✅ Merged {amazon_rows} Amazon rows.")
            merged = True
        else:
            st.warning("⚠️ Please upload Amazon files.")

        if ebay_files:
            ebay_rows = merge_ebay_files(ebay_files)
            st.success(f"✅ Merged {ebay_rows} eBay rows.")
            merged = True
        else:
            st.warning("⚠️ Please upload eBay files.")

        if merged:
            # Display merge summary chart
            df_am = pd.read_csv("merged/amazon_merged.csv")
            df_eb = pd.read_csv("merged/ebay_merged.csv")

            st.subheader("📊 Merge Summary")
            fig, ax = plt.subplots()
            ax.bar(["Amazon", "eBay"], [len(df_am), len(df_eb)], color=["#4CAF50", "#2196F3"])
            ax.set_ylabel("Rows")
            ax.set_title("Merged Keyword Counts")
            st.pyplot(fig)

            # Download merged files
            with open("merged/amazon_merged.csv", "rb") as f:
                st.download_button("📥 Download Merged Amazon CSV", f, file_name="amazon_merged.csv", mime="text/csv")
            with open("merged/ebay_merged.csv", "rb") as f:
                st.download_button("📥 Download Merged eBay CSV", f, file_name="ebay_merged.csv", mime="text/csv")

if page == "Distribute Keywords":
    st.header("📦 Distribute Keywords")
    st.write("Select a start date to generate your monthly distribution.")

    start_date = st.date_input("Start Date")

    if st.button("Distribute"):
        if os.path.exists("merged/amazon_merged.csv") and os.path.exists("merged/ebay_merged.csv"):
            result = distribute_keywords(start_date)
            if result:
                st.success(f"✅ Distributed {result['days_distributed']} day(s) into monthly ZIP.")

                # Download monthly ZIP
                if result.get("zip_path"):
                    with open(result["zip_path"], "rb") as f:
                        st.download_button(
                            "📥 Download Monthly Distribution ZIP",
                            f,
                            file_name=os.path.basename(result["zip_path"]),
                            mime="application/zip"
                        )

                # Download leftover keywords
                if result.get("amazon_download"):
                    with open(result["amazon_download"], "rb") as f:
                        st.download_button("📥 Download Undistributed Amazon CSV", f, file_name="undistributed_amazon.csv", mime="text/csv")
                if result.get("ebay_download"):
                    with open(result["ebay_download"], "rb") as f:
                        st.download_button("📥 Download Undistributed eBay CSV", f, file_name="undistributed_ebay.csv", mime="text/csv")
            else:
                st.warning("⚠️ Distribution failed.")
        else:
            st.warning("⚠️ Please merge files first.")
