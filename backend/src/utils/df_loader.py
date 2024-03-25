import os
import pandas as pd
import streamlit as st
from llama_index.core.query_engine import PandasQueryEngine
from llama_index.llms.anthropic import Anthropic
from llama_index.core import PromptTemplate
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) 

@st.cache_data()
def load_data(filename):
    df = pd.read_csv(filename)
    return df

df = load_data("backend/data/dfs/processed_brampton.csv")
st.session_state.df = df
st.write("Brampton Realestate Data")
st.write(df)

instruction_str = (
    "1. Convert the query to executable Python code using Pandas.\n"
    "2. The final line of code should be a Python expression that can be called with the `eval()` function.\n"
    "3. The code should represent a solution to the query.\n"
    "4. PRINT ONLY THE EXPRESSION.\n"
    "5. Do not quote the expression.\n"
)

pandas_prompt_str = (
    "You are working with a pandas dataframe in Python.\n"
    "The name of the dataframe is `df`.\n"
    "This is the result of `print(df.head())`:\n"
    "{df_str}\n\n"
    "Follow these instructions:\n"
    "{instruction_str}\n"
    "Query: {query_str}\n\n"
    "Expression:"
)

pandas_prompt = PromptTemplate(pandas_prompt_str).partial_format(
    instruction_str=instruction_str, df_str=df.head(5)
)
llm = Anthropic(
    model="claude-3-sonnet-20240229",
    api_key=os.getenv('ANTHROPIC_API_KEY'))

query_engine = PandasQueryEngine(df=df,
                                 llm=llm,
                                 verbose=True)

query_engine.update_prompts({"pandas_prompt": pandas_prompt})
with st.form("Question"):
    question = st.text_input("Question", value="", type="default")
    submitted = st.form_submit_button("Submit")
    if submitted:
        with st.spinner():
            response = query_engine.query(question)
            st.write("Answer:", response.response)
            st.write("Pandas query:",response.metadata['pandas_instruction_str'])
            st.write(response)