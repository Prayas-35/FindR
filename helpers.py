from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import TiDBVectorStore
from langchain_text_splitters import CharacterTextSplitter
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.llms.base import LLM
from pydantic import BaseModel
from typing import Any, List, Optional
import requests
import dotenv
import os

dotenv.load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
JABIR_API_KEY = os.getenv("JABIR_API_KEY")


class CustomConfig(BaseModel):
    api_url: str
    api_key: str


class CustomAPILLM(LLM):
    api_key: str = None
    api_url: str = None


    def __init__(self, config: CustomConfig, callbacks: Optional[List] = None):
        super().__init__()
        self.api_url = config.api_url
        self.api_key = config.api_key
        self.callbacks = callbacks or []

    @property
    def _llm_type(self) -> str:
        return "custom_api"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        headers = {
            "Content-Type": "application/json",
            "apiKey": self.api_key,
        }
        data = {"messages": [{"role": "user", "content": prompt}]}
        response = requests.post(self.api_url, json=data, headers=headers)
        response.raise_for_status()
        return response.json().get("result", {}).get("content", "")

loader = TextLoader("data.txt")
docs = loader.load()

text_splitter = CharacterTextSplitter(chunk_size=3000, chunk_overlap=500)
documents = text_splitter.split_documents(docs)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=GOOGLE_API_KEY,
)

capath = "/etc/ssl/certs/ca-certificates.crt"
vector_store = TiDBVectorStore.from_documents(
    documents=documents,
    embedding=embeddings,
    table_name="CodingGuidance",
    connection_string=f"mysql+mysqldb://2zU6uAawmvKDo4B.root:YHOr6v6CPfCNK3WI@gateway01.eu-central-1.prod.aws.tidbcloud.com:4000/test?ssl_ca={capath}",
    distance_strategy="cosine",
    drop_existing_table=True,
)

retriever = vector_store.as_retriever(score_threshold=0.5)


config = CustomConfig(
    api_url="https://api.jabirproject.org/generate",
    api_key=JABIR_API_KEY,
)
custom_llm = CustomAPILLM(config=config)