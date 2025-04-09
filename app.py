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

# === SERP Sections to Check ===
visibility_sections = [
    {"label": "Organic Results", "api_key": "organic_results", "match_field": "link"},
    {"label": "People Also Ask", "api_key": "related_questions", "match_field": "link"},
    {"label": "Popular Products", "api_key": "immersive_products", "match_field": "category", "match_value": "popular products"},
    {"label": "Knowledge Graph", "api_key": "knowledge_graph"},
    {"label": "Inline Videos", "api_key": "inline_videos", "match_field": "link"},
    {"label": "Explore Brands", "api_key": "related_brands", "match_field": "block_title", "match_value": "explore brands"},
    {"label": "People Also Buy From", "api_key": "related_brands", "match_field": "block_title", "match_value": "people also buy from"},
    {"label": "Discussion and Forums", "api_key": "discussions_and_forums", "match_field": "link"},
    {"label": "What People Are Saying", "api_key": None},
    {"label": "Shop by Store", "api_key": None}
]

def check_presence(results, section, brand_name):
    api_key = section.get("api_key")
    if not api_key or api_key not in results:
        return "-"

    data = results[api_key]
    brand_name = brand_name.lower()

    if api_key == "knowledge_graph":
        website = data.get("website")
        if website is None:
            return "-"
        return "Yes" if brand_name in website.lower() else "No"

    if isinstance(data, list):
        for item in data:
            match_field = section.get("match_field")
            match_value = section.get("match_value")

            if match_field:
                field_val = str(item.get(match_field, "")).lower()
                if match_value:
                    if match_value in field_val and brand_name in str(item).lower():
                        return "Yes"
                else:
                    if brand_name in field_val:
                        return "Yes"
            else:
                if brand_name in str(item).lower():
                    return "Yes"
        return "No"

    return "Yes" if brand_name in str(data).lower() else "No"

if run and api_key and keywords_input and brand:
    keywords = [k.strip() for k in keywords_input.split("\n") if k.strip()]
    results_list = []

    with st.spinner("🔍 Checking visibility for each keyword..."):
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

            row = {"Keyword": keyword}
            for section in visibility_sections:
                row[section["label"]] = check_presence(results, section, brand)

            row["JSON URL"] = metadata.get("json_endpoint", "-")
            row["HTML URL"] = metadata.get("raw_html_file", "-")
            results_list.append(row)
            time.sleep(1.2)

    df = pd.DataFrame(results_list)
    st.success("✅ Visibility results ready:")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"{brand}_visibility_{datetime.today().strftime('%Y-%m-%d')}.csv",
        mime='text/csv'
    )
