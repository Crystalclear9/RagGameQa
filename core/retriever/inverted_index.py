# 倒排索引
from __future__ import annotations

from collections import Counter, defaultdict
from functools import lru_cache
from typing import Any, Dict, List, Set

import jieba
import math
from sqlalchemy import func

from config.database import get_db, Document


class InvertedIndex:
    """倒排索引检索器，基于关键词匹配"""
    _cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.index = defaultdict(set)  # 词 -> 文档ID集合
        self.documents: Dict[int, Dict[str, Any]] = {}  # 文档ID -> {content, metadata}
        self.doc_freq: Dict[str, int] = {}  # 词 -> 出现的文档数
        self.doc_lengths: Dict[int, int] = {}
        self.doc_term_freqs: Dict[int, Counter[str]] = {}
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

    @staticmethod
    @lru_cache(maxsize=4096)
    def _tokenize_cached(text: str) -> tuple[str, ...]:
        words = jieba.lcut(text)
        return tuple(word for word in words if len(word) > 1)

    def _tokenize(self, text: str) -> List[str]:
        return list(self._tokenize_cached(str(text or "")))

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
            dtf = self.doc_term_freqs.get(doc_id, Counter())
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

    def _get_signature(self) -> Dict[str, Any]:
        db = None
        try:
            db = next(get_db())
            count, updated_at = (
                db.query(func.count(Document.id), func.max(Document.updated_at))
                .filter(Document.game_id == self.game_id)
                .one()
            )
            return {
                "count": int(count or 0),
                "updated_at": updated_at.isoformat() if updated_at else "",
            }
        except Exception:
            return {"count": 0, "updated_at": ""}
        finally:
            if db is not None:
                db.close()

    def _restore_cache(self, cached: Dict[str, Any]) -> None:
        self.index = cached["index"]
        self.documents = cached["documents"]
        self.doc_freq = cached["doc_freq"]
        self.doc_lengths = cached["doc_lengths"]
        self.doc_term_freqs = cached["doc_term_freqs"]
        self.avg_doc_len = cached["avg_doc_len"]

    def _build_index(self):
        """构建倒排索引（从数据库读取文档内容）"""
        signature = self._get_signature()
        cached = self._cache.get(self.game_id)
        if cached and cached.get("signature") == signature:
            self._restore_cache(cached)
            return

        db = None
        try:
            db = next(get_db())
            docs = db.query(Document).filter(Document.game_id == self.game_id).all()
            total_len = 0
            for doc in docs:
                doc_id = int(doc.id)
                text = doc.content or ""
                tokens = self._tokenize(text)
                term_freq = Counter(tokens)
                self.documents[doc_id] = {
                    'content': text,
                    'metadata': {'title': doc.title, 'source': doc.source}
                }
                self.doc_lengths[doc_id] = len(tokens)
                self.doc_term_freqs[doc_id] = term_freq
                total_len += len(tokens)

                seen = set()
                for t in term_freq:
                    self.index[t].add(doc_id)
                    if t not in seen:
                        self.doc_freq[t] = self.doc_freq.get(t, 0) + 1
                        seen.add(t)

            self.avg_doc_len = (total_len / len(docs)) if docs else 0.0
            self._cache[self.game_id] = {
                "signature": signature,
                "index": self.index,
                "documents": self.documents,
                "doc_freq": self.doc_freq,
                "doc_lengths": self.doc_lengths,
                "doc_term_freqs": self.doc_term_freqs,
                "avg_doc_len": self.avg_doc_len,
            }
        except Exception:
            # 索引构建失败则保持为空索引
            self.index = defaultdict(set)
            self.documents = {}
            self.doc_freq = {}
            self.doc_lengths = {}
            self.doc_term_freqs = {}
            self.avg_doc_len = 0.0
        finally:
            if db is not None:
                db.close()
