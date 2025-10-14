# 倒排索引
from typing import List, Dict, Any, Set
from collections import defaultdict, Counter
import jieba
import math
from config.database import get_db, Document


class InvertedIndex:
    """倒排索引检索器，基于关键词匹配"""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.index = defaultdict(set)  # 词 -> 文档ID集合
        self.documents: Dict[int, Dict[str, Any]] = {}  # 文档ID -> {content, metadata}
        self.doc_freq: Dict[str, int] = {}  # 词 -> 出现的文档数
        self.doc_lengths: Dict[int, int] = {}
        self.avg_doc_len: float = 0.0
        self._build_index()

    async def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        倒排索引检索方法

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索到的文档列表
        """
        # 1. 分词
        query_terms = self._tokenize(query)

        # 2. 查找包含查询词的文档（并集更宽松）
        candidate_docs = self._find_candidate_docs(query_terms)

        # 3. 计算BM25分数
        scored_docs = self._calculate_bm25_scores(query_terms, candidate_docs)

        # 4. 排序并返回top_k结果
        sorted_docs = sorted(scored_docs, key=lambda x: x['score'], reverse=True)

        return sorted_docs[:top_k]

    def _tokenize(self, text: str) -> List[str]:
        """文本分词"""
        words = jieba.lcut(text)
        filtered = [w for w in words if len(w) > 1]
        return filtered

    def _find_candidate_docs(self, terms: List[str]) -> Set[int]:
        """查找包含查询词的候选文档（并集）"""
        if not terms:
            return set()

        candidate: Set[int] = set()
        for term in terms:
            candidate |= set(self.index.get(term, set()))
        return candidate

    def _calculate_bm25_scores(self, query_terms: List[str], candidate_docs: Set[int]) -> List[Dict[str, Any]]:
        """计算BM25分数"""
        k1 = 1.5
        b = 0.75

        # 统计查询词频
        qtf = Counter(query_terms)
        N = max(len(self.documents), 1)

        results: List[Dict[str, Any]] = []
        for doc_id in candidate_docs:
            content = self.documents[doc_id]['content']
            title = self.documents[doc_id]['metadata'].get('title')
            source = self.documents[doc_id]['metadata'].get('source')
            dl = self.doc_lengths.get(doc_id, 1)

            score = 0.0
            # 统计文档词频
            dtf = Counter(self._tokenize(content))
            for term, qf in qtf.items():
                df = self.doc_freq.get(term, 0) or 1
                idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
                tf = dtf.get(term, 0)
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (dl / (self.avg_doc_len or 1)))
                score += idf * (numerator / (denominator or 1))

            results.append({
                'id': doc_id,
                'content': content,
                'metadata': {'title': title, 'source': source},
                'score': float(score),
                'type': 'lexical'
            })

        return results

    def _build_index(self):
        """构建倒排索引（从数据库读取文档内容）"""
        db = None
        try:
            db = next(get_db())
            docs = db.query(Document).filter(Document.game_id == self.game_id).all()

            total_len = 0
            for doc in docs:
                doc_id = int(doc.id)
                text = doc.content or ""
                tokens = self._tokenize(text)
                self.documents[doc_id] = {
                    'content': text,
                    'metadata': {'title': doc.title, 'source': doc.source}
                }
                self.doc_lengths[doc_id] = len(tokens)
                total_len += len(tokens)

                seen = set()
                for t in tokens:
                    self.index[t].add(doc_id)
                    if t not in seen:
                        self.doc_freq[t] = self.doc_freq.get(t, 0) + 1
                        seen.add(t)

            self.avg_doc_len = (total_len / len(docs)) if docs else 0.0
        except Exception:
            # 索引构建失败则保持为空索引
            self.index = defaultdict(set)
            self.documents = {}
            self.doc_freq = {}
            self.doc_lengths = {}
            self.avg_doc_len = 0.0
        finally:
            if db is not None:
                db.close()
