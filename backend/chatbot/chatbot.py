import weaviate
from langchain_community.vectorstores import Weaviate
from langchain_community.retrievers import WeaviateHybridSearchRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.docstore.document import Document
import os
from dotenv import load_dotenv
from .utils import extract_content_chunks_from_file

# Load the .env file from the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path)

# Clear existing environment variables
os.environ.pop("UPLOAD_DATA_ON_STARTUP", None)

# Retrieve the environment variables
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL", 'default-url-if-not-set')

client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=weaviate.AuthApiKey(WEAVIATE_API_KEY),
    additional_headers={
        "X-Openai-Api-Key": os.getenv("OPENAI_API_KEY"),
    },
)

try:
    print("Checking Weaviate connection...")
    client.is_ready()
    print("Connection established.")
except Exception as e:
    print("Failed to establish connection:", e)


def clear_classes():
    print("Clearing existing classes...")  # Added logging
    classes = client.schema.get()["classes"]
    for cls in classes:
        print(f"Deleting class: {cls['class']}")  # Added logging
        client.schema.delete_class(cls["class"])
    print("Existing classes cleared.")  # Added logging


def create_schema():
    print("Creating new schema...")
    schema = {
        "classes": [
            {
                "class": "LangChain",
                "vectorizer": "text2vec-openai",
                "moduleConfig": {
                    "text2vec-openai": {
                        "baseURL": "https://api.openai.com",
                        "model": "ada",
                        "vectorizeClassName": True,
                    },
                },
                "properties": [
                    {
                        "name": "text",
                        "dataType": ["text"],
                        "indexFilterable": True,
                        "indexSearchable": True,
                        "moduleConfig": {
                            "text2vec-openai": {
                                "skip": False,
                                "vectorizePropertyName": False,
                            },
                        },
                        "tokenization": "word",
                    },
                    {
                        "name": "source",
                        "dataType": ["text"],
                        "indexFilterable": True,
                        "indexSearchable": True,
                        "tokenization": "word",
                    },
                ],
            }
        ]
    }
    client.schema.create(schema)
    print("Schema created successfully.")


def upload_text_sources(file_path):
    embeddings = OpenAIEmbeddings()
    texts = extract_content_chunks_from_file(file_path)

    clear_classes()
    create_schema()

    documents = [
        {
            "text": text.page_content,
            "source": str(text.metadata)
        }
        for text in texts
    ]

    print(f"Uploading {len(documents)} documents")

    with client.batch as batch:
        for doc in documents:
            batch.add_data_object(doc, "LangChain")

    print("Documents uploaded successfully.")
    return documents

def retrieve_documents(question, top_k=5):
    retriever = WeaviateHybridSearchRetriever(
        client=client,
        index_name="LangChain",
        text_key="text",
        attributes=["text"],
        create_schema_if_missing=True,
    )

    return retriever.get_relevant_documents(question)


def ask_question(question):
    context_docs = retrieve_documents(question)
    context = "\n".join([doc.page_content for doc in context_docs])
    #print(f"context_docs: {context_docs}")
    #print(f"context: {context}")

    template = """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    Question: {question} 
    Context: {context} 
    Answer:
    """

    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    parser = StrOutputParser()

    inputs = {"context": context, "question": question}
    prompt_output = prompt.invoke(inputs)
    llm_output = llm.invoke(prompt_output) 
    answer = parser.invoke(llm_output)
    

    #    rag_chain = (
    #        inputs
    #        | prompt
    #        | llm
    #       | StrOutputParser()
    #    )
    #    answer = rag_chain.invoke(inputs)
    return answer



def check_schema():
    schema = client.schema.get()
    print("Schema:", schema)

def check_data():
    result = client.query.get('LangChain', ['text', 'source']).with_limit(10).do()
    print("DATA:", result)

def check_document_count():
    count = client.query.aggregate('LangChain').with_meta_count().do()
    print("COUNT:", count)

if __name__ == "__main__":
    check_schema()        # Verify the schema
    check_data()          # Verify data in LangChain class
    check_document_count()# Check document count
    # Re-upload documents
    file_path = "backend/chatbot/paca.html"
    retriever = upload_text_sources(file_path)
    input_text = input("Enter your question: ")
    answer = ask_question(input_text)
    print(answer)
