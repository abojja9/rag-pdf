import os
import pickle
from pyprojroot import here
from llama_index.core.settings import Settings
from llama_index_client import Document
from llama_index.core.agent import ReActAgent
from llama_index.core.schema import IndexNode
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core import load_index_from_storage, ServiceContext, StorageContext, VectorStoreIndex, SummaryIndex
from llama_index.core.retrievers.auto_merging_retriever import AutoMergingRetriever
from llama_index.core.indices.postprocessor import SentenceTransformerRerank
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes  # Added HierarchicalNodeParser import
from backend.src.settings import CFG, get_embeddings, get_llm
from rich import print
from typing import List, Dict

def get_meta(file_path):
    fname, ext = file_path.split("/")[-1].split(".")
    metadata = {
        "title": fname,
        "file_path": file_path,
        "file_name": fname,
        "file_type": ext,
        "file_size": os.path.getsize(file_path),
        "creation_date": os.path.getctime(file_path),
        "last_modified_date": os.path.getmtime(file_path),
        "last_accessed_date": os.path.getatime(file_path),
    }
    return metadata

def parse_documents(filename):
    if os.getenv("LLAMA_CLOUD_API_KEY") is None:
        raise ValueError(
            "LLAMA_CLOUD_API_KEY environment variable is not set. "
            "Please set it in .env file or in your shell environment then run again!"
        )
    parser = LlamaParse(result_type="markdown", verbose=True, language="en")
    reader = SimpleDirectoryReader(
        CFG.documents_dir,
        file_metadata=get_meta,
        file_extractor={".pdf": parser},
    )
    documents = reader.load_data()

    
    with open(os.path.join(CFG.parsed_documents_dir, filename), 'wb') as f:
        pickle.dump(documents, f)
        print(f"Documents saved to {os.path.join(CFG.parsed_documents_dir, filename)}")
    return documents

def get_documents(filename="documents.pkl"):
    if not os.path.exists(CFG.parsed_documents_dir):
        os.makedirs(CFG.parsed_documents_dir)
    
    if os.path.exists(os.path.join(CFG.parsed_documents_dir, filename)):
        with open(os.path.join(CFG.parsed_documents_dir, filename), 'rb') as f:
            documents = pickle.load(f)
            print(f"Documents loaded from {os.path.join(CFG.parsed_documents_dir, filename)}")
            return documents
    else:
        return parse_documents(filename)

def init_settings():
    Settings.llm = get_llm()
    Settings.embed_model = get_embeddings()
    Settings.chunk_size = CFG.chunk_sizes
    Settings.chunk_overlap = CFG.chunk_overlap

    
def build_index(documents: List[Document], filename: str):
    chunk_sizes = CFG.chunk_sizes
    # create hierarchical node parser   
    node_parser = HierarchicalNodeParser.from_defaults(chunk_sizes=chunk_sizes)
    # get nodes from documents
    nodes = node_parser.get_nodes_from_documents(documents)
    # get leaf nodes
    leaf_nodes = get_leaf_nodes(nodes)
    # create service context
    service_context = ServiceContext.from_defaults(
        llm=Settings.llm, 
        embed_model=Settings.embed_model)
    # create document store with nodes
    docstore = SimpleDocumentStore()
    docstore.add_documents(nodes)
    storage_context = StorageContext.from_defaults(
        docstore=docstore
    )
    persist_dir = CFG.save_dir
    print(f"Persist_dir location: {persist_dir}")
    if not os.path.exists(persist_dir):
        print(f"Creating the location: {persist_dir}")
        vector_index = VectorStoreIndex(
            leaf_nodes,
            storage_context=storage_context,
            service_context=service_context,
            persist_dir=persist_dir
        )
    else:
        vector_index = load_index_from_storage(
            StorageContext.from_defaults(persist_dir=persist_dir),
            service_context=service_context,
        )
    # creating a summary index
    summary_index = SummaryIndex(nodes, service_context=service_context)
    
    return vector_index, summary_index
    
def build_query_engines(
    vector_index: VectorStoreIndex,
    summary_index: SummaryIndex,
    similarity_top_k: int = 5,
    rerank_top_n: int = 2,
    use_rerank: bool = False,
    filename: str = None,
):
    # creating a retriever
    base_retriever = vector_index.as_retriever(similarity_top_k=similarity_top_k)
    vector_retriever = AutoMergingRetriever(
        base_retriever,
        vector_index.storage_context,
        verbose=True)
    if use_rerank:
        rerank = SentenceTransformerRerank(
            top_n=rerank_top_n, model="BAAI/bge-reranker-base"
        )
        vector_query_engine = RetrieverQueryEngine.from_args(
            vector_retriever, 
            node_postprocessors=[rerank]
        )
    else:
        vector_query_engine = RetrieverQueryEngine.from_args(
            vector_retriever
        )
    summary_query_engine = summary_index.as_query_engine()
    
    query_engine_tools = [
            QueryEngineTool(
                query_engine=vector_query_engine,
                metadata=ToolMetadata(
                    name="vector_tool",
                    description=(
                        f"Useful for specific questions related to the contents of {filename}. "
                        "Use this tool to answer questions that require detailed information or context "
                        "from the document. The answers should be based solely on the information present "
                        "in this specific document."
                    ),
                ),
            ),
            QueryEngineTool(
                query_engine=summary_query_engine,
                metadata=ToolMetadata(
                    name="summary_tool",
                    description=(
                        f"Useful for requests that require a high-level summary or overview of {filename}. "
                        "Use this tool when you need a concise summary or general understanding of the document's content."
                    ),
                ),
            ),
        ]
    # build agent
    agent = ReActAgent.from_tools(
        query_engine_tools,
        llm=Settings.llm,
        verbose=True,
    )
    
    return agent, vector_query_engine, summary_query_engine


def build_react_agent_query_engine(agent: ReActAgent, filename: str):
    summary = (
        f"Use this index to answer questions related to the document {filename}. "
        "For questions that require detailed information or context from the document, "
        "use the vector_tool. For questions that require a high-level summary or overview, "
        "use the summary_tool."
    )
    objects= []
    node = IndexNode(
        text=summary, index_id=filename, obj=agent
    )
    objects.append(node)
    vector_index = VectorStoreIndex(
    objects=objects,
    )
    query_engine = vector_index.as_query_engine(similarity_top_k=5, verbose=True)
    return query_engine
    
    
print("config:", CFG)

init_settings()
# filename='tax_documents.pkl'
# documents = get_documents(filename)
# vector_index, summary_index = build_index(documents=documents, filename=documents[0].metadata["file_name"])
# high_level_agent, vector_query_engine, summary_query_engine = build_query_engines(
#     vector_index,
#     summary_index,
#     use_rerank=True,
#     filename=documents[0].metadata["file_name"])
# react_agent_query_engine = build_react_agent_query_engine(high_level_agent, filename=documents[0].metadata["file_name"])

# AI / ML report under Clause 9 (v) of Chapter IV of the 
# Master Circular for Custodians
questions = [
    "what is the summary of the document?",
    "what is the periodicity of the AI / ML report under Clause 9 (v) of Chapter IV?",
    "what's the deadline for the investor grievance report?",
    "what is the SEBI  circular number for the subject 'Streamlining  of"
    " Regulatory  Reporting  by  Designated  Depository Participants (DDPs) and Custodians'?",
    "what was the date when the circular NSDL/POLICY/DDP/2024/0002 was issued?",
    "what is circular SEBI/HO/AFD/ AFD-SEC-2/P/CIR/2024/8 about?",
]

# for question in questions:
#     # print(react_agent_query_engine.query(question).response)
#     print(question)
#     # print(vector_query_engine.query(question).response)
#     print(high_level_agent.chat(question).response)
#     print("===========")
    

