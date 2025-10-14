# 社区爬虫
from typing import List, Dict, Any, Optional
import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class CommunityCrawler:
    """社区平台爬虫"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.session = None
        logger.info(f"社区爬虫初始化完成: {game_id}")
    
    async def crawl(self, max_pages: int = 100) -> List[Dict[str, Any]]:
        """爬取社区数据"""
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
                
                logger.info(f"社区爬虫完成，获取{len(all_data)}条数据")
                return all_data
                
        except Exception as e:
            logger.error(f"社区爬虫执行失败: {str(e)}")
            return []
    
    def _build_crawl_urls(self, max_pages: int) -> List[str]:
        """构建爬取URL列表"""
        urls = []
        
        # NGA论坛
        urls.append(f"https://nga.178.com/wow")
        
        # 贴吧
        urls.append(f"https://tieba.baidu.com/f?kw={self.game_id}")
        
        # Reddit
        urls.append(f"https://www.reddit.com/r/{self.game_id}")
        
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
            
            # 根据URL类型选择解析方法
            if 'nga.178.com' in url:
                data.extend(self._parse_nga(soup))
            elif 'tieba.baidu.com' in url:
                data.extend(self._parse_tieba(soup))
            elif 'reddit.com' in url:
                data.extend(self._parse_reddit(soup))
            
            return data
            
        except Exception as e:
            logger.error(f"页面解析失败: {str(e)}")
            return []
    
    def _parse_nga(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """解析NGA论坛"""
        posts = []
        
        try:
            post_elements = soup.find_all('div', class_='post')
            
            for post_elem in post_elements:
                post = {
                    'source': 'nga',
                    'type': 'forum_post',
                    'content': '',
                    'metadata': {}
                }
                
                # 提取帖子标题
                title_elem = post_elem.find('div', class_='post-title')
                if title_elem:
                    post['content'] = title_elem.get_text().strip()
                
                # 提取帖子内容
                content_elem = post_elem.find('div', class_='post-content')
                if content_elem:
                    post['content'] += ' ' + content_elem.get_text().strip()
                
                if post['content']:
                    posts.append(post)
            
        except Exception as e:
            logger.error(f"NGA解析失败: {str(e)}")
        
        return posts
    
    def _parse_tieba(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """解析百度贴吧"""
        posts = []
        
        try:
            post_elements = soup.find_all('div', class_='threadlist_title')
            
            for post_elem in post_elements:
                post = {
                    'source': 'tieba',
                    'type': 'forum_post',
                    'content': '',
                    'metadata': {}
                }
                
                # 提取帖子标题
                title_elem = post_elem.find('a')
                if title_elem:
                    post['content'] = title_elem.get_text().strip()
                
                if post['content']:
                    posts.append(post)
            
        except Exception as e:
            logger.error(f"贴吧解析失败: {str(e)}")
        
        return posts
    
    def _parse_reddit(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """解析Reddit"""
        posts = []
        
        try:
            post_elements = soup.find_all('div', class_='post')
            
            for post_elem in post_elements:
                post = {
                    'source': 'reddit',
                    'type': 'forum_post',
                    'content': '',
                    'metadata': {}
                }
                
                # 提取帖子标题
                title_elem = post_elem.find('h3')
                if title_elem:
                    post['content'] = title_elem.get_text().strip()
                
                if post['content']:
                    posts.append(post)
            
        except Exception as e:
            logger.error(f"Reddit解析失败: {str(e)}")
        
        return posts
    
    async def incremental_crawl(self, last_update_time: str) -> List[Dict[str, Any]]:
        """增量爬取"""
        return await self.crawl(max_pages=10)