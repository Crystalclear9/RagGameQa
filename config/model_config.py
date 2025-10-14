# 模型配置文件
from typing import Dict, List, Any


class ModelConfig:
    """模型配置类

    统一管理各类模型的可选配置，并提供便捷的查询与校验方法。
    """

    # RAG模型配置
    RAG_MODELS = {
        "deepseek-r1": {
            "model_name": "deepseek-ai/DeepSeek-R1",
            "max_tokens": 100000,
            "temperature": 0.7,
            "top_p": 0.9
        },
        "gpt-4": {
            "model_name": "gpt-4",
            "max_tokens": 8000,
            "temperature": 0.7,
            "top_p": 0.9
        }
    }

    # 嵌入模型配置
    EMBEDDING_MODELS = {
        "sentence-transformers": {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "dimension": 384,
            "max_length": 512
        },
        "multilingual": {
            "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "dimension": 384,
            "max_length": 512
        }
    }

    # 分类模型配置
    CLASSIFICATION_MODELS = {
        "bert": {
            "model_name": "bert-base-chinese",
            "num_labels": 8,
            "max_length": 512
        },
        "bilstm": {
            "hidden_size": 256,
            "num_layers": 2,
            "dropout": 0.3
        }
    }

    # 多模态模型配置
    MULTIMODAL_MODELS = {
        "asr": {
            "model_name": "wav2vec2-base",
            "sampling_rate": 16000,
            "language": "zh"
        },
        "tts": {
            "model_name": "tts-models/zh-CN/baker/tacotron2-DDC-GST",
            "sampling_rate": 22050
        },
        "image_caption": {
            "model_name": "Salesforce/blip2-opt-2.7b",
            "max_length": 100
        }
    }

    # 类型到配置映射，便于统一查询
    _TYPE_TO_CONFIG: Dict[str, Dict[str, Any]] = {
        "rag": RAG_MODELS,
        "embedding": EMBEDDING_MODELS,
        "classification": CLASSIFICATION_MODELS,
        "multimodal": MULTIMODAL_MODELS,
    }

    @classmethod
    def get_model_config(cls, model_type: str, model_name: str) -> Dict[str, Any]:
        """获取指定模型配置

        Args:
            model_type: 模型类型（rag | embedding | classification | multimodal）
            model_name: 具体模型名称key

        Returns:
            对应模型配置，不存在则返回空字典
        """
        model_type = (model_type or "").strip().lower()
        config_pool = cls._TYPE_TO_CONFIG.get(model_type, {})
        return config_pool.get(model_name, {})

    @classmethod
    def list_models(cls, model_type: str) -> List[str]:
        """列出某类可用模型名称列表"""
        model_type = (model_type or "").strip().lower()
        return list(cls._TYPE_TO_CONFIG.get(model_type, {}).keys())

    @classmethod
    def has_model(cls, model_type: str, model_name: str) -> bool:
        """判断指定模型是否存在"""
        return model_name in cls._TYPE_TO_CONFIG.get((model_type or "").strip().lower(), {})
