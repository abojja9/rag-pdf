import yaml
from pyprojroot import here
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())  # read local .env file


class LoadConfig:

    def __init__(self) -> None:
        with open(here("backend/configs/config.yml")) as cfg:
            app_config = yaml.load(cfg, Loader=yaml.FullLoader)

        self.documents_dir: str = here(f"backend/{app_config['documents_dir']}")
        self.save_dir: str = here(f"backend/{app_config['save_dir']}")
        self.parsed_documents_dir: str = here(f"backend/{app_config['parsed_documents_dir']}")
        # llm
        self.llm_type: str = app_config["llm_cfg"]["llm_type"]
        self.gpt_model: str = app_config["llm_cfg"]["gpt_model"]
        self.google_model: str = app_config["llm_cfg"]["gemini_model"]
        self.anthropic_model: str = app_config["llm_cfg"]["anthropic_model"]
        
        # temp
        self.temperature: float = app_config["llm_cfg"]["temperature"]
        # self.max_tokens: int = app_config["llm_cfg"]["max_tokens"]
        # embedding model
        self.embed_model_name: str = app_config["llm_cfg"]["embed_model_name"]
        self.rerank_model: str = app_config["llm_cfg"]["rerank_model"]

        # basic_rag
        self.basic_rag_index_save_dir: str = app_config["llama_index_cfg"]["basic_rag"]["index_save_dir"]

        # pagewise_rag
        self.pagewise_rag_index_save_dir: str = app_config[
            "llama_index_cfg"]["pagewise_rag"]["index_save_dir"]

        # sentence_retrieval
        self.sentence_index_save_dir: str = app_config[
            "llama_index_cfg"]["sentence_retrieval"]["index_save_dir"]
        self.sentence_window_size: int = app_config["llama_index_cfg"][
            "sentence_retrieval"]["sentence_window_size"]
        self.sentence_retrieval_similarity_top_k: int = app_config["llama_index_cfg"][
            "sentence_retrieval"]["similarity_top_k"]
        self.sentence_retrieval_rerank_top_n: int = app_config[
            "llama_index_cfg"]["sentence_retrieval"]["rerank_top_n"]

        # auto_merging_retrieval
        self.auto_merging_retrieval_index_save_dir: str = app_config["llama_index_cfg"][
            "auto_merging_retrieval"]["index_save_dir"]
        self.chunk_sizes: list = app_config["llama_index_cfg"]["auto_merging_retrieval"]["chunk_sizes"]
        self.chunk_overlap: int = app_config["llama_index_cfg"]["auto_merging_retrieval"]["chunk_overlap"]
        self.auto_merging_retrieval_similarity_top_k: int = app_config["llama_index_cfg"][
            "auto_merging_retrieval"]["similarity_top_k"]
        self.auto_merging_retrieval_rerank_top_n: int = app_config["llama_index_cfg"][
            "auto_merging_retrieval"]["rerank_top_n"]