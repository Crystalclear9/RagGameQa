# 领域适配器
from typing import List, Dict, Any, Optional

class DomainAdapter:
    """领域适配器，将通用知识适配到特定游戏领域"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.game_config = self._load_game_config()
    
    async def adapt(
        self, 
        context_docs: List[Dict[str, Any]], 
        user_context: Optional[Dict] = None
    ) -> str:
        """
        适配领域知识
        
        Args:
            context_docs: 原始上下文文档
            user_context: 用户上下文
            
        Returns:
            适配后的上下文
        """
        # 1. 过滤相关文档
        relevant_docs = self._filter_relevant_docs(context_docs, user_context)
        
        # 2. 转换文档格式
        formatted_docs = self._format_documents(relevant_docs)
        
        # 3. 添加游戏特定信息
        enhanced_context = self._enhance_with_game_info(formatted_docs)
        
        return enhanced_context
    
    def _filter_relevant_docs(self, docs: List[Dict], user_context: Optional[Dict]) -> List[Dict]:
        """过滤相关文档"""
        if not user_context:
            return docs
        
        # 根据用户偏好过滤文档
        filtered_docs = []
        for doc in docs:
            if self._is_relevant(doc, user_context):
                filtered_docs.append(doc)
        
        return filtered_docs
    
    def _format_documents(self, docs: List[Dict]) -> str:
        """格式化文档"""
        formatted_text = ""
        for i, doc in enumerate(docs, 1):
            formatted_text += f"文档{i}：\n"
            formatted_text += f"内容：{doc['content']}\n"
            if 'metadata' in doc:
                formatted_text += f"来源：{doc['metadata'].get('source', '未知')}\n"
            formatted_text += "\n"
        
        return formatted_text
    
    def _enhance_with_game_info(self, context: str) -> str:
        """添加游戏特定信息"""
        game_info = self.game_config.get('game_info', {})
        enhanced_context = f"游戏：{game_info.get('name', self.game_id)}\n"
        enhanced_context += f"版本：{game_info.get('version', '未知')}\n\n"
        enhanced_context += context
        return enhanced_context
    
    def _is_relevant(self, doc: Dict, user_context: Dict) -> bool:
        """判断文档是否相关"""
        # 根据用户等级、偏好等判断相关性
        return True
    
    def _load_game_config(self) -> Dict:
        """加载游戏配置"""
        # 从配置文件加载游戏特定配置
        return {}
