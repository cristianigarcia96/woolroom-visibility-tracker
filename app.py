import streamlit as st
from serpapi import GoogleSearch
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="SERP Visibility Tracker", layout="wide")

# === Sidebar UI ===
st.sidebar.title("🔍 SERP Visibility Tracker")
st.sidebar.markdown("Track your brand's visibility across Google SERP features.")

api_key = st.sidebar.text_input("🔐 SerpAPI Key", type="password")
brand = st.sidebar.text_input("🏷️ Brand Name to Track")
keywords_input = st.sidebar.text_area("📝 Keywords (one per line)")
run = st.sidebar.button("🚀 Run Visibility Check")

# === Feature labeling overrides and type mapping ===
feature_map = {
    "related_searches": ("Related searches", "non-traditional"),
    "knowledge_graph": ("Knowledge panel", "non-traditional"),
    "organic_results": ("Organic results", "traditional"),
    "inline_videos": ("Videos", "non-traditional"),
    "ads": ("Ads", "non-traditional"),
    "shopping_results": ("Shopping results", "non-traditional"),
    "immersive_products": ("Popular products", "non-traditional"),
    "people_also_ask": ("People Also Ask", "non-traditional"),
    "discussions_and_forums": ("Discussions and forums", "non-traditional")
}

weights = {
    "traditional": 1,
    "non-traditional": 0.5
}

def compute_score(row):
    t = row['Traditional Count'] * weights['traditional']
    n = row['Non-Traditional Count'] * weights['non-traditional']
    return t + n

def compute_grade(score):
    if score >= 2.5:
        return "A"
    elif score >= 2.0:
        return "B"
    elif score >= 1.5:
        return "C"
    elif score >= 1.0:
        return "D"
    else:
        return "F"

st.markdown("""
    <style>
        .main .block-container {
            padding-top: 2rem;
        }
        .stDataFrame thead tr th {
            background-color: #f4f4f4;
        }
        .stDownloadButton button {
            background-color: #4CAF50;
            color: white;
        }
        .stButton button {
            background-color: #1f77b4;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

if run and api_key and keywords_input and brand:
    keywords = [k.strip() for k in keywords_input.split("\n") if k.strip()]
    summary_results = []

    with st.spinner("🔍 Running visibility checks across keywords..."):
        for keyword in keywords:
            params = {
                "q": keyword,
                "hl": "en",
                "gl": "us",
                "api_key": api_key
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            metadata = results.get("search_metadata", {})

            serp_presence = {"traditional": 0, "non-traditional": 0}
            seen_features = set()

            for item in results.get("organic_results", []):
                if brand.lower() in str(item).lower():
                    serp_presence["traditional"] += 1
                    seen_features.add("Organic results")
                    break

            def search_features(data, path=""):
                if isinstance(data, dict):
                    for k, v in data.items():
                        if k == "organic_results":
                            continue

                        new_path = f"{path}::{k}" if path else k

                        if k == "immersive_products" and isinstance(v, list):
                            for item in v:
                                if brand.lower() in str(item).lower():
                                    label, ftype = feature_map.get(k, (k, "non-traditional"))
                                    serp_presence[ftype] += 1
                                    seen_features.add(label)

                        elif isinstance(v, (dict, list)):
                            search_features(v, new_path)
                        elif isinstance(v, str) and brand.lower() in v.lower():
                            label_key = next((p for p in path.split("::") if p in feature_map), path.split("::")[-1])
                            label, ftype = feature_map.get(label_key, (label_key, "non-traditional"))
                            serp_presence[ftype] += 1
                            seen_features.add(label)

                elif isinstance(data, list):
                    for item in data:
                        search_features(item, path)

            search_features(results)

            score = compute_score(serp_presence)
            grade = compute_grade(score)

            summary_results.append({
                "Keyword": keyword,
                "Traditional Count": serp_presence["traditional"],
                "Non-Traditional Count": serp_presence["non-traditional"],
                "Score": round(score, 2),
                "Grade": grade,
                "JSON URL": metadata.get("json_endpoint", "-"),
                "HTML URL": metadata.get("raw_html_file", "-")
            })

            time.sleep(1.2)

    if summary_results:
        df = pd.DataFrame(summary_results)
        st.success("✅ Visibility scoring summary:")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"visibility_score_{brand}_{datetime.today().strftime('%Y-%m-%d')}.csv",
            mime='text/csv',
            key="download-csv"
        )
    else:
        st.warning("⚠️ No brand mentions found in SERP features.")
