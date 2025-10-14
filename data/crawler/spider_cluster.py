# 分布式爬虫集群
from typing import List, Dict, Any, Optional
import asyncio
import logging
from .steam_crawler import SteamCrawler
from .epic_crawler import EpicCrawler
from .community_crawler import CommunityCrawler

logger = logging.getLogger(__name__)

class SpiderCluster:
    """分布式爬虫集群"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.crawlers = {
            'steam': SteamCrawler(game_id),
            'epic': EpicCrawler(game_id),
            'community': CommunityCrawler(game_id)
        }
        logger.info(f"爬虫集群初始化完成: {game_id}")
    
    async def crawl_all_sources(self, max_pages: int = 100) -> List[Dict[str, Any]]:
        """
        爬取所有数据源
        
        Args:
            max_pages: 最大页数
            
        Returns:
            爬取的数据列表
        """
        try:
            tasks = []
            
            # 并行爬取所有数据源
            for crawler_name, crawler in self.crawlers.items():
                task = asyncio.create_task(
                    crawler.crawl(max_pages),
                    name=f"crawl_{crawler_name}"
                )
                tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 合并结果
            all_data = []
            for i, result in enumerate(results):
                crawler_name = list(self.crawlers.keys())[i]
                
                if isinstance(result, Exception):
                    logger.error(f"{crawler_name}爬虫失败: {str(result)}")
                else:
                    all_data.extend(result)
                    logger.info(f"{crawler_name}爬虫完成，获取{len(result)}条数据")
            
            logger.info(f"爬虫集群完成，总共获取{len(all_data)}条数据")
            return all_data
            
        except Exception as e:
            logger.error(f"爬虫集群执行失败: {str(e)}")
            return []
    
    async def crawl_specific_source(self, source: str, max_pages: int = 100) -> List[Dict[str, Any]]:
        """
        爬取指定数据源
        
        Args:
            source: 数据源名称
            max_pages: 最大页数
            
        Returns:
            爬取的数据列表
        """
        try:
            if source not in self.crawlers:
                logger.error(f"不支持的数据源: {source}")
                return []
            
            crawler = self.crawlers[source]
            data = await crawler.crawl(max_pages)
            
            logger.info(f"{source}爬虫完成，获取{len(data)}条数据")
            return data
            
        except Exception as e:
            logger.error(f"{source}爬虫执行失败: {str(e)}")
            return []
    
    async def incremental_crawl(self, last_update_time: str) -> List[Dict[str, Any]]:
        """
        增量爬取
        
        Args:
            last_update_time: 上次更新时间
            
        Returns:
            新增数据列表
        """
        try:
            tasks = []
            
            for crawler_name, crawler in self.crawlers.items():
                task = asyncio.create_task(
                    crawler.incremental_crawl(last_update_time),
                    name=f"incremental_{crawler_name}"
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            all_data = []
            for i, result in enumerate(results):
                crawler_name = list(self.crawlers.keys())[i]
                
                if isinstance(result, Exception):
                    logger.error(f"{crawler_name}增量爬取失败: {str(result)}")
                else:
                    all_data.extend(result)
                    logger.info(f"{crawler_name}增量爬取完成，获取{len(result)}条新数据")
            
            return all_data
            
        except Exception as e:
            logger.error(f"增量爬取失败: {str(e)}")
            return []
    
    def get_crawler_stats(self) -> Dict[str, Any]:
        """获取爬虫统计信息"""
        stats = {
            'game_id': self.game_id,
            'total_crawlers': len(self.crawlers),
            'crawler_types': list(self.crawlers.keys())
        }
        
        for name, crawler in self.crawlers.items():
            stats[f'{name}_status'] = 'active'
        
        return stats