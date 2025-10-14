# 向量检索器
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from config.database import get_db, Document
import ast


class VectorRetriever:
    """向量检索器，基于语义相似度检索"""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    async def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        向量检索方法

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索到的文档列表
        """
        # 1. 将查询转换为向量 (1, d) -> (d,)
        query_vector = self.model.encode([query])[0]

        # 2. 在向量存储中搜索相似文档
        similar_docs = await self._search_similar(query_vector, top_k)

        # 3. 直接返回候选（含score）
        return similar_docs

    async def _search_similar(self, query_vector: np.ndarray, top_k: int) -> List[Dict]:
        """在向量存储中搜索相似文档（批量相似度；可选FAISS兜底）"""
        db = None
        try:
            db = next(get_db())
            docs = db.query(Document).filter(Document.game_id == self.game_id).all()

            # 收集向量与元数据
            vectors: List[np.ndarray] = []
            meta: List[Dict[str, Any]] = []
            for doc in docs:
                if not getattr(doc, 'embedding', None):
                    continue
                try:
                    vec = np.array(ast.literal_eval(doc.embedding), dtype=float)
                    if vec.ndim != 1:
                        continue
                    vectors.append(vec)
                    meta.append({
                        'id': doc.id,
                        'content': doc.content,
                        'metadata': {'source': doc.source, 'title': doc.title},
                    })
                except Exception:
                    continue

            if not vectors:
                return []

            mat = np.vstack(vectors)  # [N, d]

            # 尝试使用FAISS（若安装）
            try:
                import faiss  # type: ignore
                dim = mat.shape[1]
                # 归一化到单位向量使内积等于余弦
                mat_norm = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12)
                q = (query_vector / (np.linalg.norm(query_vector) + 1e-12)).astype('float32')
                index = faiss.IndexFlatIP(dim)
                index.add(mat_norm.astype('float32'))
                D, I = index.search(q.reshape(1, -1), min(top_k, mat_norm.shape[0]))
                scored: List[Dict] = []
                for score, idx in zip(D[0], I[0]):
                    if idx == -1:
                        continue
                    m = meta[int(idx)]
                    scored.append({
                        'id': m['id'],
                        'content': m['content'],
                        'metadata': m['metadata'],
                        'score': float(score),
                        'type': 'vector'
                    })
                return scored
            except Exception:
                # NUMPY向量化余弦相似
                q = query_vector
                mat_norms = np.linalg.norm(mat, axis=1) + 1e-12
                qn = np.linalg.norm(q) + 1e-12
                sims = (mat @ q) / (mat_norms * qn)
                top_idx = np.argsort(-sims)[:top_k]
                scored = []
                for idx in top_idx:
                    m = meta[int(idx)]
                    scored.append({
                        'id': m['id'],
                        'content': m['content'],
                        'metadata': m['metadata'],
                        'score': float(sims[int(idx)]),
                        'type': 'vector'
                    })
                return scored
        except Exception:
            return []
        finally:
            if db is not None:
                db.close()

    def _calculate_similarity(self, query_vector: np.ndarray, doc_vector: np.ndarray) -> float:
        """计算余弦相似度"""
        if query_vector is None or doc_vector is None:
            return 0.0
        q = np.array(query_vector)
        d = np.array(doc_vector)
        qn = np.linalg.norm(q)
        dn = np.linalg.norm(d)
        if qn == 0 or dn == 0:
            return 0.0
        return float(np.dot(q, d) / (qn * dn))
