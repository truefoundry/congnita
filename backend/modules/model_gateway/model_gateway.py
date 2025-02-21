import os
from typing import List

import yaml
from cachetools import Cache
from langchain.embeddings.base import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from pandasai.llm.local_llm import LocalLLM

from backend.logger import logger
from backend.modules.model_gateway.audio_processing_svc import AudioProcessingSvc
from backend.modules.model_gateway.reranker_svc import InfinityRerankerSvc
from backend.settings import settings
from backend.types import ModelConfig, ModelProviderConfig, ModelType

# Maximum number of model instances to cache
MAX_CACHE_SIZE = 50

# Helper function to create a fixed-size cache
# Returns: Cache object with specified max size
create_cache = lambda: Cache(maxsize=MAX_CACHE_SIZE)


class ModelGateway:
    """
    Gateway class for managing and accessing different types of ML models.
    Handles model initialization, caching, and configuration management.
    """

    def __init__(self):
        """
        Initialize the ModelGateway with caches for different model types
        and load model configurations from YAML file.

        Caches:
            _embedder_cache: Stores embedding model instances
            _llm_cache: Stores LLM model instances
            _reranker_cache: Stores reranking model instances
            _audio_cache: Stores audio model instances
        """
        self._embedder_cache = create_cache()
        self._llm_cache = create_cache()
        self._pandas_ai_cache = create_cache()
        self._reranker_cache = create_cache()
        self._audio_cache = create_cache()

        # Load configs and initialize models
        logger.info(f"Loading models config from {settings.MODELS_CONFIG_PATH}")
        with open(settings.MODELS_CONFIG_PATH) as f:
            data = yaml.safe_load(f)
        logger.info(f"Loaded models config: {data}")

        self.provider_configs = [
            ModelProviderConfig.model_validate(item)
            for item in data.get("model_providers", [])
        ]

        self.model_name_to_provider_config = {}
        self.llm_models: List[ModelConfig] = []
        self.embedding_models: List[ModelConfig] = []
        self.reranker_models: List[ModelConfig] = []
        self.audio_models: List[ModelConfig] = []

        self._initialize_models()

    def _initialize_models(self):
        """
        Initialize all model providers and validate their API keys.

        Raises:
            ValueError: If required API key environment variables are not set
        """
        for provider_config in self.provider_configs:
            if provider_config.api_key_env_var and not os.environ.get(
                provider_config.api_key_env_var
            ):
                raise ValueError(
                    f"Environment variable {provider_config.api_key_env_var} not set. "
                    f"Cannot initialize the model gateway."
                )

            self._register_models(provider_config)

    def _register_models(self, provider_config: ModelProviderConfig):
        """
        Register models from a provider config into their respective type lists.

        This method creates a mapping between model types and their corresponding
        configuration attributes and storage lists. For each model type:
        1. Gets the list of model IDs from the provider config
        2. Creates a fully qualified model name (provider/model_id)
        3. Maps the model name to its provider config
        4. Adds a new ModelConfig to the appropriate type-specific list

        Args:
            provider_config (ModelProviderConfig): Configuration for a model provider
                containing model IDs for different types (embedding, chat, reranking, audio)

        Examples:
            For a provider config with:
                provider_name: "openai"
                embedding_model_ids: ["text-embedding-3-small"]
                llm_model_ids: ["gpt-4", "gpt-3.5-turbo"]
                reranking_model_ids: ["rerank-english-v2.0"]
                audio_model_ids: ["whisper-1"]

            Creates the following ModelConfigs:

            1. Embedding model:
                name: "openai/text-embedding-3-small"
                type: ModelType.embedding
                -> Added to self.embedding_models

            2. LLM models:
                name: "openai/gpt-4"
                type: ModelType.chat
                -> Added to self.llm_models

                name: "openai/gpt-3.5-turbo"
                type: ModelType.chat
                -> Added to self.llm_models

            3. Reranking model:
                name: "openai/rerank-english-v2.0"
                type: ModelType.reranking
                -> Added to self.reranker_models

            4. Audio model:
                name: "openai/whisper-1"
                type: ModelType.audio
                -> Added to self.audio_models

            Each model name is also mapped in self.model_name_to_provider_config to
            its provider configuration for later access to API keys and base URLs.
        """
        # Combined mapping of model types to their attributes and lists
        model_mappings = {
            ModelType.embedding: ("embedding_model_ids", self.embedding_models),
            ModelType.chat: ("llm_model_ids", self.llm_models),
            ModelType.reranking: ("reranking_model_ids", self.reranker_models),
            ModelType.audio: ("audio_model_ids", self.audio_models),
        }

        # Process each model type using the mapping
        for model_type, (attr_name, model_list) in model_mappings.items():
            model_ids = getattr(provider_config, attr_name, [])
            for model_id in model_ids:
                model_name = f"{provider_config.provider_name}/{model_id}"
                self.model_name_to_provider_config[model_name] = provider_config
                model_list.append(ModelConfig(name=model_name, type=model_type))

    def _get_api_key(self, provider_config: ModelProviderConfig) -> str:
        """
        Get API key for a model provider from environment variables.

        Args:
            provider_config (ModelProviderConfig): Provider configuration containing
                API key environment variable name

        Returns:
            str: API key if found, "EMPTY" if no key needed, or empty string if not found
        """
        if not provider_config.api_key_env_var:
            return "EMPTY"
        return os.environ.get(provider_config.api_key_env_var, "")

    def get_embedding_models(self) -> List[ModelConfig]:
        """
        Getter function for embedding models.
        """
        return self.embedding_models

    def get_llm_models(self) -> List[ModelConfig]:
        """
        Getter function for LLM models.
        """
        return self.llm_models

    def get_reranker_models(self) -> List[ModelConfig]:
        """
        Getter function for reranker models.
        """
        return self.reranker_models

    def get_audio_models(self) -> List[ModelConfig]:
        """
        Getter function for audio models.
        """
        return self.audio_models

    def get_embedder_from_model_config(self, model_name: str) -> Embeddings:
        """
        Get an embedder instance for the specified model name. Uses caching to avoid
        recreating embedder instances for the same model.

        Args:
            model_name (str): Name of the embedding model in format "provider/model_id"

        Returns:
            Embeddings: A LangChain Embeddings instance configured for the specified model

        Raises:
            ValueError: If the model name is not registered in the model gateway

        Cache behavior:
            Caches embedder instances in self._embedder_cache using model_name as key.
            Subsequent calls with same model_name return cached instance.
        """
        if model_name not in self._embedder_cache:
            if model_name not in self.model_name_to_provider_config:
                raise ValueError(
                    f"Model {model_name} not registered in the model gateway."
                )

            provider_config = self.model_name_to_provider_config[model_name]
            api_key = self._get_api_key(provider_config)
            model_id = "/".join(model_name.split("/")[1:])

            self._embedder_cache[model_name] = OpenAIEmbeddings(
                openai_api_key=api_key,
                model=model_id,
                openai_api_base=provider_config.base_url,
                check_embedding_ctx_length=(provider_config.provider_name == "openai"),
            )

        return self._embedder_cache[model_name]

    def get_llm_from_model_config(
        self, model_config: ModelConfig, stream=False
    ) -> BaseChatModel:
        """
        Get a language model instance for the specified model configuration. Uses caching to avoid
        recreating LLM instances for the same model and stream settings.

        Args:
            model_config (ModelConfig): Configuration object containing model name and parameters
            stream (bool, optional): Whether to enable streaming responses. Defaults to False.

        Returns:
            BaseChatModel: A LangChain chat model instance configured according to the model_config

        Raises:
            ValueError: If the model name is not registered in the model gateway

        Cache behavior:
            Caches LLM instances in self._llm_cache using (model_name, stream) tuple as key.
            Subsequent calls with same model_config and stream setting return cached instance.
        """
        cache_key = (model_config.name, stream)
        if cache_key not in self._llm_cache:
            if model_config.name not in self.model_name_to_provider_config:
                raise ValueError(
                    f"Model {model_config.name} not registered in the model gateway."
                )

            provider_config = self.model_name_to_provider_config[model_config.name]
            api_key = self._get_api_key(provider_config)
            model_id = "/".join(model_config.name.split("/")[1:])

            parameters = model_config.parameters or {}
            self._llm_cache[cache_key] = ChatOpenAI(
                model=model_id,
                temperature=parameters.get("temperature", 0.1),
                max_tokens=parameters.get("max_tokens", 1024),
                streaming=stream,
                api_key=api_key,
                base_url=provider_config.base_url,
                default_headers=provider_config.default_headers,
            )

        return self._llm_cache[cache_key]

    def get_pandas_ai_model_from_model_config(self, model_config: ModelConfig):
        """
        Get a PandasAI model instance for the specified model configuration.
        """
        cache_key = model_config.name
        if cache_key not in self._pandas_ai_cache:
            if model_config.name not in self.model_name_to_provider_config:
                raise ValueError(
                    f"Model {model_config.name} not registered in the model gateway."
                )

            provider_config = self.model_name_to_provider_config[model_config.name]
            api_key = self._get_api_key(provider_config)
            model_id = "/".join(model_config.name.split("/")[1:])

            self._pandas_ai_cache[cache_key] = LocalLLM(
                api_base=provider_config.base_url, model=model_id, api_key=api_key
            )

        return self._pandas_ai_cache[cache_key]

    def get_reranker_from_model_config(self, model_name: str, top_k: int = 3):
        """
        Get a reranker model instance for the specified model configuration. Uses caching to avoid
        recreating reranker instances for the same model and top_k settings.

        Args:
            model_name (str): Name of the reranker model to use
            top_k (int, optional): Number of top results to return. Defaults to 3.

        Returns:
            InfinityRerankerSvc: A reranker service instance configured according to the model name
                                and top_k parameter

        Raises:
            ValueError: If the model name is not registered in the model gateway

        Cache behavior:
            Caches reranker instances in self._reranker_cache using (model_name, top_k) tuple as key.
            Subsequent calls with same model name and top_k setting return cached instance.
        """
        cache_key = (model_name, top_k)
        if cache_key not in self._reranker_cache:
            if model_name not in self.model_name_to_provider_config:
                raise ValueError(
                    f"Model {model_name} not registered in the model gateway."
                )

            provider_config = self.model_name_to_provider_config[model_name]
            api_key = self._get_api_key(provider_config)
            model_id = "/".join(model_name.split("/")[1:])

            self._reranker_cache[cache_key] = InfinityRerankerSvc(
                model=model_id,
                api_key=api_key,
                base_url=provider_config.base_url,
                top_k=top_k,
            )

        return self._reranker_cache[cache_key]

    def get_audio_model_from_model_config(self, model_name: str):
        """
        Get an audio processing model instance for the specified model configuration. Uses caching to avoid
        recreating audio model instances for the same model settings.

        Args:
            model_name (str): Name of the audio model to use, in format "provider/model"

        Returns:
            AudioProcessingSvc: An audio processing service instance configured according to the model name

        Raises:
            ValueError: If the model name is not registered in the model gateway

        Cache behavior:
            Caches audio model instances in self._audio_cache using model_name as key.
            Subsequent calls with same model name return cached instance.
        """
        if model_name not in self._audio_cache:
            if model_name not in self.model_name_to_provider_config:
                raise ValueError(
                    f"Model {model_name} not registered in the model gateway."
                )

            provider_config = self.model_name_to_provider_config[model_name]
            api_key = self._get_api_key(provider_config)
            _, model = model_name.split("/", 1)

            self._audio_cache[model_name] = AudioProcessingSvc(
                api_key=api_key,
                base_url=provider_config.base_url,
                model=model,
            )

        return self._audio_cache[model_name]


model_gateway = ModelGateway()
