# Epic爬虫
from typing import List, Dict, Any

class EpicCrawler:
    """Epic平台爬虫"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
    
    async def crawl(self) -> List[Dict[str, Any]]:
        """爬取Epic数据"""
        pass
