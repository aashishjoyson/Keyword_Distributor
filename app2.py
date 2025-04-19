import streamlit as st
from utils.merge import merge_amazon_files, merge_ebay_files
from utils.distribute import distribute_keywords
from PIL import Image
import os
import pandas as pd
import plotly.express as px

# App configuration
st.set_page_config(page_title="Keyword Distributor", layout="wide")

# --- Header with logo and title ---
logo = Image.open(os.path.join("utils", "logo.png"))
col1, col2 = st.columns([1, 5])
with col1:
    st.image(logo, width=120)
with col2:
    st.markdown("# 📦 Keyword Distributor", unsafe_allow_html=True)

st.markdown(
    """
    Welcome to **Keyword Distributor**! 🚀

    **What You Can Do:**
    - 🔄 Merge multiple Amazon & eBay keyword CSVs
    - 📊 Visualize merge counts & distributions
    - 🗂️ Distribute into 20‑account daily folders
    - 📦 Download as monthly ZIP
    - 💾 Download leftover keywords
    """
)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Merge Files", "Distribute Keywords"])

# Ensure necessary folders exist per session
for folder in ["uploads", "merged", "distributed", "leftover"]:
    os.makedirs(folder, exist_ok=True)

# --- Merge Files Page ---
if page == "Merge Files":
    st.header("🛠️ Merge Amazon & eBay Files")
    st.write("Upload CSVs with columns: `Keyword`, `Link`.")

    amazon_files = st.file_uploader("Amazon CSVs", accept_multiple_files=True, key="amazon")
    ebay_files   = st.file_uploader("eBay CSVs", accept_multiple_files=True, key="ebay")

    if st.button("Merge Files"):
        if not amazon_files and not ebay_files:
            st.warning("Please upload at least one file to merge.")
        else:
            if amazon_files:
                amazon_rows = merge_amazon_files(amazon_files)
                st.success(f"✅ Merged {amazon_rows} Amazon rows.")
            if ebay_files:
                ebay_rows = merge_ebay_files(ebay_files)
                st.success(f"✅ Merged {ebay_rows} eBay rows.")

            # Interactive bar chart for merge summary
            df_am = pd.read_csv("merged/amazon_merged.csv")
            df_eb = pd.read_csv("merged/ebay_merged.csv")
            fig_bar = px.bar(
                x=["Amazon","eBay"],
                y=[len(df_am), len(df_eb)],
                labels={"x":"Platform", "y":"Rows"},
                title="Merged Keyword Counts",
                color=["Amazon","eBay"],
                color_discrete_map={"Amazon":"#4CAF50","eBay":"#2196F3"}
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # Download buttons
            with open("merged/amazon_merged.csv","rb") as f:
                st.download_button("📥 Download Merged Amazon CSV", f, file_name="amazon_merged.csv")
            with open("merged/ebay_merged.csv","rb") as f:
                st.download_button("📥 Download Merged eBay CSV", f, file_name="ebay_merged.csv")

# --- Distribute Keywords Page ---
if page == "Distribute Keywords":
    st.header("📦 Distribute Keywords")
    st.write("Select a start date to generate your monthly distribution.")
    start_date = st.date_input("Start Date")

    if st.button("Distribute"):
        if os.path.exists("merged/amazon_merged.csv") and os.path.exists("merged/ebay_merged.csv"):
            result = distribute_keywords(start_date)
            if result:
                # Summary metrics
                am_total = result['amazon_distributed'] + result['remaining_amazon']
                eb_total = result['ebay_distributed'] + result['remaining_ebay']
                colA, colB, colC = st.columns(3)
                colA.metric("Amazon Distributed", f"{result['amazon_distributed']}/{am_total}")
                colB.metric("eBay Distributed",   f"{result['ebay_distributed']}/{eb_total}")
                colC.metric("Days Distributed",    result['days_distributed'])

                # Interactive pie charts
                st.subheader("Distribution vs Leftover")
                fig_pie_am = px.pie(
                    names=["Distributed","Leftover"],
                    values=[result['amazon_distributed'], result['remaining_amazon']],
                    title="Amazon Distribution",
                    hole=0.4
                )
                fig_pie_eb = px.pie(
                    names=["Distributed","Leftover"],
                    values=[result['ebay_distributed'], result['remaining_ebay']],
                    title="eBay Distribution",
                    hole=0.4
                )
                st.plotly_chart(fig_pie_am, use_container_width=True)
                st.plotly_chart(fig_pie_eb, use_container_width=True)

                # Sunburst chart
                st.subheader("Sunburst Overview")
                pie_df = pd.DataFrame({
                    "Platform":["Amazon","Amazon","eBay","eBay"],
                    "Type":["Distributed","Leftover","Distributed","Leftover"],
                    "Count":[
                        result['amazon_distributed'],
                        result['remaining_amazon'],
                        result['ebay_distributed'],
                        result['remaining_ebay']
                    ]
                })
                sunb = px.sunburst(
                    pie_df,
                    path=['Platform','Type'],
                    values='Count',
                    color='Platform',
                    title="Keyword Distribution Overview"
                )
                sunb.update_traces(textinfo='label+percent entry')
                st.plotly_chart(sunb, use_container_width=True)

                # Daily trend line chart
                if 'daily_distribution' in result:
                    st.subheader("Daily Distribution Trend")
                    df_daily = pd.DataFrame(result['daily_distribution'])
                    line = px.line(
                        df_daily,
                        x='date',
                        y=['amazon','ebay'],
                        labels={'value':'Keywords','variable':'Platform','date':'Date'},
                        title="Daily Distributed Keywords"
                    )
                    st.plotly_chart(line, use_container_width=True)

                # Detailed table
                if 'daily_distribution' in result:
                    st.subheader("Detailed Daily Distribution")
                    st.dataframe(
                        df_daily.assign(date=df_daily['date'].dt.strftime('%Y-%m-%d'))
                    )
            else:
                st.warning("Distribution failed. Please merge files first.")
        else:
            st.warning("Please merge files first.")
