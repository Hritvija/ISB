import streamlit as st
import sqlite3
import pandas as pd
from llama_cpp import Llama
import os

# === 1. Load SQLite database ===
DB_PATH = "C:\\Users\\singh\\.spyder-py3\\survey_isb.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# === 2. Load the Unquantized GGUF LLM ===
MODEL_PATH = "D:/gguf/codellama-nl2sql.Q4_K_M.gguf"  # <--- Your merged model
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=12  # Adjust based on your CPU
)

# === 3. Dynamic Schema Extraction ===
def get_schema():
    schema = ""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    for (table,) in tables:
        schema += f"Table: {table}\n"
        cursor.execute(f"PRAGMA table_info({table});")
        for col in cursor.fetchall():
            col_name = col[1]
            col_type = col[2]
            nullable = "NULLABLE" if col[3] == 0 else "NOT NULL"
            schema += f"    {col_name} ({col_type}, {nullable})\n"
        schema += "\n"
    return schema

# === 4. NL to SQL Prompt & Response ===
def generate_sql(nl_query, schema):
    llm_context = f"""You are an expert SQLite analyst.
You must only use table and column names that exist in the schema below:

{schema}

role_id Mapping (from Roles table):
- 1 = Focal Manager
- 2 = Subordinate
- 3 = Reporting Manager

Use only valid SQLite syntax. Do NOT use MySQL/Postgres features like ILIKE, LIMIT, AUTO_INCREMENT, etc.

If a question cannot be answered using this schema and role mapping, respond with:
"I cannot answer this query."

Always return a single valid SQLite SELECT query only.
"""

    prompt = llm_context + f"\nUser query: {nl_query}\nSQLite query:"
    output = llm(prompt, max_tokens=512, stop=["###"])
    output_text = output['choices'][0]['text'].strip() 
    first_statement = output_text.split(";")[0].strip() + ";"
    sql_code = first_statement





    # Optional: validation check
    if not sql_code.upper().startswith("SELECT"):
        raise ValueError("Invalid SQL output: Not a SELECT")

    return sql_code

# === 5. Streamlit Dashboard ===
# === Connection to DB ===
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# === UI ===
st.set_page_config(page_title="🧠 NL2SQL with CodeLLaMA", layout="wide")
st.title("🧠 NL2SQL Dashboard — Fine-tuned GGUF Model")
st.markdown("Enter a natural language query below. The model will convert it into valid **SQLite** SQL.")

nl_query = st.text_input("Ask a question about your survey data:")

if st.button("Generate SQL"):
    schema = get_schema()
    try:
        sql = generate_sql(nl_query, schema)
        st.code(sql, language="sql")

        df = pd.read_sql_query(sql, conn)
        st.dataframe(df)

    except ValueError as ve:
        st.error(f"SQL Error: {ve}")
    except Exception as e:
        st.error(f"Database error: {e}")


