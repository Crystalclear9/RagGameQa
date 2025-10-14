# 知识库管理器
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.orm import Session
from config.database import get_db, Document, Game
from core.knowledge_base.embedding_service import EmbeddingService
from core.knowledge_base.semantic_compression import SemanticCompression

logger = logging.getLogger(__name__)

class KnowledgeBaseManager:
    """知识库管理器"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.embedding_service = EmbeddingService()
        self.semantic_compression = SemanticCompression()
        logger.info(f"知识库管理器初始化完成: {game_id}")
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        添加文档到知识库
        
        Args:
            documents: 文档列表
            
        Returns:
            是否添加成功
        """
        try:
            db = next(get_db())
            
            for doc_data in documents:
                # 生成嵌入向量
                embedding = await self.embedding_service.encode_text(doc_data.get('content', ''))
                
                # 创建文档记录
                document = Document(
                    game_id=self.game_id,
                    content=doc_data.get('content', ''),
                    title=doc_data.get('title', ''),
                    category=doc_data.get('category', ''),
                    source=doc_data.get('source', ''),
                    metadata=str(doc_data.get('metadata', {})),
                    embedding=str(embedding.tolist())
                )
                
                db.add(document)
            
            db.commit()
            logger.info(f"成功添加{len(documents)}个文档到知识库")
            return True
            
        except Exception as e:
            logger.error(f"添加文档失败: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()
    
    async def search_documents(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        搜索文档
        
        Args:
            query: 查询文本
            top_k: 返回数量
            
        Returns:
            文档列表
        """
        try:
            db = next(get_db())
            
            # 生成查询向量
            query_embedding = await self.embedding_service.encode_text(query)
            
            # 搜索相似文档
            documents = db.query(Document).filter(
                Document.game_id == self.game_id
            ).all()
            
            # 计算相似度并排序
            results = []
            for doc in documents:
                if doc.embedding:
                    doc_embedding = eval(doc.embedding)  # 解析存储的向量
                    similarity = self._calculate_similarity(query_embedding, doc_embedding)
                    
                    results.append({
                        'id': doc.id,
                        'content': doc.content,
                        'title': doc.title,
                        'category': doc.category,
                        'source': doc.source,
                        'metadata': eval(doc.metadata) if doc.metadata else {},
                        'similarity': similarity
                    })
            
            # 按相似度排序
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"搜索文档失败: {str(e)}")
            return []
        finally:
            db.close()
    
    async def update_document(self, doc_id: int, updates: Dict[str, Any]) -> bool:
        """
        更新文档
        
        Args:
            doc_id: 文档ID
            updates: 更新内容
            
        Returns:
            是否更新成功
        """
        try:
            db = next(get_db())
            
            document = db.query(Document).filter(
                Document.id == doc_id,
                Document.game_id == self.game_id
            ).first()
            
            if not document:
                return False
            
            # 更新字段
            for key, value in updates.items():
                if hasattr(document, key):
                    setattr(document, key, value)
            
            # 如果内容更新，重新生成嵌入
            if 'content' in updates:
                embedding = await self.embedding_service.encode_text(updates['content'])
                document.embedding = str(embedding.tolist())
            
            db.commit()
            logger.info(f"成功更新文档: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新文档失败: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()
    
    async def delete_document(self, doc_id: int) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            是否删除成功
        """
        try:
            db = next(get_db())
            
            document = db.query(Document).filter(
                Document.id == doc_id,
                Document.game_id == self.game_id
            ).first()
            
            if not document:
                return False
            
            db.delete(document)
            db.commit()
            logger.info(f"成功删除文档: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()
    
    async def compress_knowledge_base(self) -> Dict[str, Any]:
        """
        压缩知识库
        
        Returns:
            压缩结果统计
        """
        try:
            db = next(get_db())
            
            # 获取所有文档
            documents = db.query(Document).filter(
                Document.game_id == self.game_id
            ).all()
            
            # 执行语义压缩
            compressed_docs = await self.semantic_compression.compress_documents(documents)
            
            # 更新压缩后的文档
            for i, doc in enumerate(documents):
                if i < len(compressed_docs):
                    doc.content = compressed_docs[i]['content']
                    doc.metadata = str(compressed_docs[i]['metadata'])
            
            db.commit()
            
            result = {
                'original_count': len(documents),
                'compressed_count': len(compressed_docs),
                'compression_ratio': len(compressed_docs) / len(documents) if documents else 0
            }
            
            logger.info(f"知识库压缩完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"知识库压缩失败: {str(e)}")
            return {}
        finally:
            db.close()
    
    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        import numpy as np
        
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            db = next(get_db())
            
            total_docs = db.query(Document).filter(
                Document.game_id == self.game_id
            ).count()
            
            categories = db.query(Document.category).filter(
                Document.game_id == self.game_id
            ).distinct().all()
            
            return {
                'game_id': self.game_id,
                'total_documents': total_docs,
                'categories': [cat[0] for cat in categories if cat[0]],
                'embedding_service': type(self.embedding_service).__name__,
                'compression_service': type(self.semantic_compression).__name__
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}
        finally:
            db.close()