import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="🧠 NL2SQL Dashboard", layout="wide")
st.title("🧠 NL2SQL Dashboard (FastAPI Backend)")
st.markdown("Enter a natural language query. This will be sent to a FastAPI backend that calls CodeLLaMA to generate SQL.")

nl_query = st.text_input("Ask a question about your survey data:")

if st.button("Generate SQL"):
    try:
        res = requests.post("http://localhost:8000/query", json={"query": nl_query})
        if res.status_code == 200:
            data = res.json()
            st.code(data["sql"], language="sql")
            st.dataframe(pd.DataFrame(data["data"]))
        else:
            st.error("❌ Error: " + res.json().get("detail", "Unknown error"))
    except Exception as e:
        st.error(f"❌ Server error: {e}")