import streamlit as st
from utils.merge import process_uploaded_files
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
    - 🔄 Upload and merge six marketplace keyword CSVs
    - 📊 Visualize merge counts & distributions
    - 🗂️ Distribute into 23‑account daily folders
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
    st.header("🛠️ Upload & Merge Marketplace Files")
    st.write("Upload six keyword CSV files (amazon_us, ebay, amazon_de, amazon_uk, amazon_ca, amazon_au)")

    uploaded_files = st.file_uploader("Upload Marketplace CSVs", accept_multiple_files=True)

    if st.button("Merge Files"):
        if not uploaded_files:
            st.warning("Please upload at least one file.")
        else:
            merge_summary = process_uploaded_files(uploaded_files)
            st.success(f"✅ Successfully merged {merge_summary['total_files']} files.")

            # Bar chart for merged row counts
            fig_bar = px.bar(
                x=list(merge_summary['row_counts'].keys()),
                y=list(merge_summary['row_counts'].values()),
                labels={"x":"Platform", "y":"Rows"},
                title="Merged Keyword Counts",
                color=list(merge_summary['row_counts'].keys()),
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # Download links for merged files
            for platform, path in merge_summary['saved_paths'].items():
                with open(path, "rb") as f:
                    st.download_button(f"📥 Download Merged {platform}.csv", f, file_name=f"{platform}.csv")

# --- Distribute Keywords Page ---
if page == "Distribute Keywords":
    st.header("📦 Distribute Keywords")
    st.write("Select a start date to generate your monthly distribution.")
    start_date = st.date_input("Start Date")

    if st.button("Distribute"):
        result = distribute_keywords(start_date)
        if result:
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Days Distributed", result['days_distributed'])
            col2.metric("Total Accounts Per Day", "23")
            col3.metric("Rows Per File", "100")

            # Download ZIP
            with open(result['zip_path'], 'rb') as f:
                st.download_button(
                    "📥 Download Monthly Distribution ZIP",
                    f,
                    file_name=os.path.basename(result['zip_path']),
                    mime="application/zip"
                )

            # Download leftovers
            st.subheader("Leftover Keywords")
            for platform, leftover_path in result['leftover_paths'].items():
                if leftover_path:
                    with open(leftover_path, 'rb') as f:
                        st.download_button(f"📥 Download Leftover {platform}.csv", f, file_name=f"leftover_{platform}.csv")

            # Pie Charts
            st.subheader("Distribution vs Leftover by Platform")
            pie_data = pd.DataFrame({
                "Platform": list(result['distribution_stats'].keys()),
                "Distributed": [v['distributed'] for v in result['distribution_stats'].values()],
                "Leftover": [v['leftover'] for v in result['distribution_stats'].values()]
            })
            for _, row in pie_data.iterrows():
                fig_pie = px.pie(
                    names=["Distributed", "Leftover"],
                    values=[row["Distributed"], row["Leftover"]],
                    title=f"{row['Platform']} Distribution",
                    hole=0.4
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            # Daily Distribution Trend
            st.subheader("Daily Distribution Trend")
            df_daily = pd.DataFrame(result['daily_distribution'])
            df_daily['date'] = df_daily['date'].astype(str)
            line = px.line(
                df_daily,
                x='date',
                y=[col for col in df_daily.columns if col != 'date'],
                labels={'value':'Keywords','variable':'Platform','date':'Date'},
                title="Daily Distributed Keywords"
            )
            st.plotly_chart(line, use_container_width=True)

            st.subheader("Detailed Daily Distribution Table")
            st.dataframe(df_daily)
        else:
            st.warning("Distribution failed. Please ensure files are merged first.")
