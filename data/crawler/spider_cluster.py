# 分布式爬虫集群
from typing import List, Dict, Any
import asyncio
from data.crawler.steam_crawler import SteamCrawler
from data.crawler.epic_crawler import EpicCrawler
from data.crawler.community_crawler import CommunityCrawler

class SpiderCluster:
    """分布式爬虫集群"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.crawlers = {
            'steam': SteamCrawler(game_id),
            'epic': EpicCrawler(game_id),
            'community': CommunityCrawler(game_id)
        }
    
    async def crawl_all_sources(self) -> List[Dict[str, Any]]:
        """爬取所有数据源"""
        tasks = []
        for crawler in self.crawlers.values():
            tasks.append(crawler.crawl())
        
        results = await asyncio.gather(*tasks)
        
        # 合并所有结果
        all_data = []
        for result in results:
            all_data.extend(result)
        
        return all_data
