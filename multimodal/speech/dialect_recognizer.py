# 方言识别器
from typing import Dict, Any, List
import logging
import re

logger = logging.getLogger(__name__)

class DialectRecognizer:
    """方言识别器"""
    
    def __init__(self):
        # 方言特征词库
        self.dialect_patterns = {
            'cantonese': {
                'words': ['嘅', '咗', '咁', '唔', '係', '嘅', '咩', '嘞', '啲', '佢'],
                'phrases': ['唔该', '多谢', '点解', '做乜', '点样']
            },
            'sichuanese': {
                'words': ['啥', '咋', '嘛', '噻', '哈', '撒', '嘛', '噻'],
                'phrases': ['啥子', '咋个', '做啥', '咋样', '哈子']
            },
            'northeastern': {
                'words': ['咋', '啥', '整', '整啥', '咋整'],
                'phrases': ['咋整', '整啥', '干啥', '咋样']
            }
        }
        
        logger.info("方言识别器初始化完成")
    
    async def recognize_dialect(self, text: str) -> Dict[str, Any]:
        """
        识别方言类型
        
        Args:
            text: 输入文本
            
        Returns:
            方言识别结果
        """
        try:
            if not text.strip():
                return {'dialect': 'standard', 'confidence': 0.0}
            
            # 计算各方言的匹配分数
            dialect_scores = {}
            
            for dialect, patterns in self.dialect_patterns.items():
                score = self._calculate_dialect_score(text, patterns)
                dialect_scores[dialect] = score
            
            # 找到最高分的方言
            if dialect_scores:
                best_dialect = max(dialect_scores, key=dialect_scores.get)
                best_score = dialect_scores[best_dialect]
                
                # 如果分数太低，认为是标准普通话
                if best_score < 0.1:
                    best_dialect = 'standard'
                    best_score = 0.0
            else:
                best_dialect = 'standard'
                best_score = 0.0
            
            result = {
                'dialect': best_dialect,
                'confidence': best_score,
                'all_scores': dialect_scores
            }
            
            logger.info(f"方言识别完成: {best_dialect} (置信度: {best_score:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"方言识别失败: {str(e)}")
            return {'dialect': 'standard', 'confidence': 0.0}
    
    def _calculate_dialect_score(self, text: str, patterns: Dict[str, List[str]]) -> float:
        """计算方言匹配分数"""
        try:
            score = 0.0
            total_words = len(text)
            
            if total_words == 0:
                return 0.0
            
            # 计算特征词匹配
            word_matches = 0
            for word in patterns.get('words', []):
                word_matches += text.count(word)
            
            # 计算短语匹配
            phrase_matches = 0
            for phrase in patterns.get('phrases', []):
                phrase_matches += text.count(phrase)
            
            # 计算分数（短语权重更高）
            score = (word_matches * 1.0 + phrase_matches * 3.0) / total_words
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"方言分数计算失败: {str(e)}")
            return 0.0
    
    async def adapt_text_for_dialect(self, text: str, dialect: str) -> str:
        """
        根据方言适配文本
        
        Args:
            text: 原始文本
            dialect: 方言类型
            
        Returns:
            适配后的文本
        """
        try:
            if dialect == 'standard':
                return text
            
            # 方言到标准普通话的转换
            dialect_mappings = {
                'cantonese': {
                    '嘅': '的',
                    '咗': '了',
                    '咁': '这么',
                    '唔': '不',
                    '係': '是',
                    '咩': '什么',
                    '嘞': '了',
                    '啲': '一些',
                    '佢': '他/她'
                },
                'sichuanese': {
                    '啥': '什么',
                    '咋': '怎么',
                    '嘛': '吗',
                    '噻': '吧',
                    '哈': '啊'
                }
            }
            
            if dialect in dialect_mappings:
                mappings = dialect_mappings[dialect]
                adapted_text = text
                
                for dialect_word, standard_word in mappings.items():
                    adapted_text = adapted_text.replace(dialect_word, standard_word)
                
                return adapted_text
            
            return text
            
        except Exception as e:
            logger.error(f"方言文本适配失败: {str(e)}")
            return text
    
    def get_supported_dialects(self) -> List[str]:
        """获取支持的方言列表"""
        return list(self.dialect_patterns.keys()) + ['standard']
    
    def get_dialect_features(self, dialect: str) -> Dict[str, Any]:
        """获取方言特征"""
        if dialect in self.dialect_patterns:
            return self.dialect_patterns[dialect]
        elif dialect == 'standard':
            return {'words': [], 'phrases': []}
        else:
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'supported_dialects': self.get_supported_dialects(),
            'total_patterns': sum(len(patterns['words']) + len(patterns['phrases']) 
                                for patterns in self.dialect_patterns.values())
        }