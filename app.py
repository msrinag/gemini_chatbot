import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
import google.generativeai as palm
import base64
from langchain_community.utilities import SQLDatabase
# Initialize Gemini 1.5 (PaLM) API (replace with your API initialization code)

palm.configure(api_key=base64.b64decode("QUl6YVN5QlEtQVFTTUhGSjMyQ0NEME10OUpxVTdFUzdCbVEtSFNN".encode()).decode())

def connectDatabase(username, port, host, password, database):
    mysql_uri = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
    st.session_state.db = SQLDatabase.from_uri(mysql_uri)

def runQuery(query):
    return st.session_state.db.run(query) if st.session_state.db else "Please connect to the database"

def getDatabaseSchema():
    return st.session_state.db.get_table_info() if st.session_state.db else "Please connect to the database"

# Use Gemini (PaLM) for generating SQL queries
def getQueryFromLLM(question):
    template = """Below is the schema of a MYSQL database. Read the schema carefully and answer the user's question with an SQL query, taking care of table and column name case sensitivity.

    {schema}

    Please provide only the SQL query.

    For example:
    Question: How many albums do we have in the database?
    SQL query: SELECT COUNT(*) FROM album;
    Question: How many customers are from Brazil in the database?
    SQL query: SELECT COUNT(*) FROM customer WHERE country = 'Brazil';

    Your turn:
    Question: {question}
    SQL query:"""

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | palm

    response = chain.invoke({
        "question": question,
        "schema": getDatabaseSchema()
    })
    return response['content']

def getResponseForQueryResult(question, query, result):
    template2 = """Below is the schema of a MYSQL database. Write a natural language response based on the SQL query and result.

    {schema}

    Example:
    Question: How many albums do we have in the database?
    SQL query: SELECT COUNT(*) FROM album;
    Result: [(34,)]
    Response: There are 34 albums in the database.

    Your turn:
    Question: {question}
    SQL query: {query}
    Result: {result}
    Response:"""

    prompt2 = ChatPromptTemplate.from_template(template2)
    chain2 = prompt2 | palm

    response = chain2.invoke({
        "question": question,
        "schema": getDatabaseSchema(),
        "query": query,
        "result": result
    })

    return response['content']

# Streamlit UI
st.set_page_config(page_icon="🤖", page_title="Chat with MYSQL DB", layout="centered")

question = st.chat_input('Chat with your MYSQL database')

if "chat" not in st.session_state:
    st.session_state.chat = []

if question:
    if "db" not in st.session_state:
        st.error('Please connect to the database first.')
    else:
        st.session_state.chat.append({
            "role": "user",
            "content": question
        })

        query = getQueryFromLLM(question)
        print(query)
        result = runQuery(query)
        print(result)
        response = getResponseForQueryResult(question, query, result)
        st.session_state.chat.append({
            "role": "assistant",
            "content": response
        })

for chat in st.session_state.chat:
    st.chat_message(chat['role']).markdown(chat['content'])

# Sidebar for Database Connection
with st.sidebar:
    st.title('Connect to Database')
    st.text_input(label="Host", key="host", value="localhost")
    st.text_input(label="Port", key="port", value="3306")
    st.text_input(label="Username", key="username", value="root")
    st.text_input(label="Password", key="password", value="", type="password")
    st.text_input(label="Database", key="database", value="rag_test")
    connectBtn = st.button("Connect")

if connectBtn:
    connectDatabase(
        username=st.session_state.username,
        port=st.session_state.port,
        host=st.session_state.host,
        password=st.session_state.password,
        database=st.session_state.database,
    )
    st.success("Database connected")
