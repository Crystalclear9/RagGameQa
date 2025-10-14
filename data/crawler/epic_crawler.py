# Epic爬虫
from typing import List, Dict, Any, Optional
import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class EpicCrawler:
    """Epic Games平台爬虫"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.base_url = "https://store.epicgames.com"
        self.session = None
        logger.info(f"Epic爬虫初始化完成: {game_id}")
    
    async def crawl(self, max_pages: int = 100) -> List[Dict[str, Any]]:
        """爬取Epic数据"""
        try:
            async with aiohttp.ClientSession() as session:
                self.session = session
                
                urls = self._build_crawl_urls(max_pages)
                all_data = []
                
                for url in urls:
                    try:
                        data = await self._crawl_page(url)
                        all_data.extend(data)
                        await asyncio.sleep(1)
                    except Exception as e:
                        logger.error(f"爬取页面失败 {url}: {str(e)}")
                
                logger.info(f"Epic爬虫完成，获取{len(all_data)}条数据")
                return all_data
                
        except Exception as e:
            logger.error(f"Epic爬虫执行失败: {str(e)}")
            return []
    
    def _build_crawl_urls(self, max_pages: int) -> List[str]:
        """构建爬取URL列表"""
        urls = []
        
        # Epic商店页面
        urls.append(f"{self.base_url}/zh-CN/p/{self.game_id}")
        
        # Epic社区页面
        urls.append(f"{self.base_url}/zh-CN/p/{self.game_id}/community")
        
        return urls[:max_pages]
    
    async def _crawl_page(self, url: str) -> List[Dict[str, Any]]:
        """爬取单个页面"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_page(html, url)
                else:
                    logger.warning(f"页面访问失败: {url}, 状态码: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"页面爬取失败: {url}, 错误: {str(e)}")
            return []
    
    def _parse_page(self, html: str, url: str) -> List[Dict[str, Any]]:
        """解析页面内容"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            data = []
            
            # 解析游戏信息
            game_info = self._extract_game_info(soup)
            if game_info:
                data.append(game_info)
            
            # 解析用户评论
            reviews = self._extract_reviews(soup)
            data.extend(reviews)
            
            return data
            
        except Exception as e:
            logger.error(f"页面解析失败: {str(e)}")
            return []
    
    def _extract_game_info(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """提取游戏信息"""
        try:
            game_info = {
                'source': 'epic',
                'type': 'game_info',
                'content': '',
                'metadata': {}
            }
            
            # 提取游戏描述
            desc_elem = soup.find('div', class_='game-description')
            if desc_elem:
                game_info['content'] = desc_elem.get_text().strip()
            
            return game_info
            
        except Exception as e:
            logger.error(f"游戏信息提取失败: {str(e)}")
            return None
    
    def _extract_reviews(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """提取用户评论"""
        reviews = []
        
        try:
            review_elements = soup.find_all('div', class_='review-item')
            
            for review_elem in review_elements:
                review = {
                    'source': 'epic',
                    'type': 'review',
                    'content': '',
                    'metadata': {}
                }
                
                # 提取评论内容
                content_elem = review_elem.find('div', class_='review-content')
                if content_elem:
                    review['content'] = content_elem.get_text().strip()
                
                if review['content']:
                    reviews.append(review)
            
        except Exception as e:
            logger.error(f"评论提取失败: {str(e)}")
        
        return reviews
    
    async def incremental_crawl(self, last_update_time: str) -> List[Dict[str, Any]]:
        """增量爬取"""
        return await self.crawl(max_pages=10)