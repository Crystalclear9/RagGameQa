# 模型配置文件
from typing import Dict, List, Any

class ModelConfig:
    """模型配置类"""
    
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
    
    @classmethod
    def get_model_config(cls, model_type: str, model_name: str) -> Dict[str, Any]:
        """获取指定模型配置"""
        if model_type in cls.RAG_MODELS:
            return cls.RAG_MODELS.get(model_name, {})
        elif model_type in cls.EMBEDDING_MODELS:
            return cls.EMBEDDING_MODELS.get(model_name, {})
        elif model_type in cls.CLASSIFICATION_MODELS:
            return cls.CLASSIFICATION_MODELS.get(model_name, {})
        elif model_type in cls.MULTIMODAL_MODELS:
            return cls.MULTIMODAL_MODELS.get(model_name, {})
        else:
            return {}
