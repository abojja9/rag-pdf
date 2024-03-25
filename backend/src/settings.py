from llama_index.llms.anthropic import Anthropic
from llama_index.llms.gemini import Gemini
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from backend.src.load_config import LoadConfig
CFG = LoadConfig()

def get_llm_fn():
    if CFG.llm_type == "anthropic":
        model_fn = Anthropic
        llm_model = CFG.anthropic_model
    elif CFG.llm_type == "google":
        model_fn = Gemini
        llm_model = CFG.google_model
    elif CFG.llm_type == "openai":
        model_fn = OpenAI
        llm_model = CFG.gpt_model
    return model_fn, llm_model
    
def get_llm():
    llm_fn, llm_model = get_llm_fn()
    config = {
        "model": llm_model,
        "temperature": float(CFG.temperature),
    }
    return llm_fn(**config)

def get_embeddings():
    return HuggingFaceEmbedding(CFG.embed_model_name)


