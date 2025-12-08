"""
Platform Tools - Handles posting to various social media platforms
"""
import os
from typing import Dict, List
from abc import ABC, abstractmethod
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BasePlatformTool(ABC):
    """Base class for all platform posting tools"""
    
    def __init__(self):
        self.authenticated = False
        self._load_credentials()
    
    @abstractmethod
    def _load_credentials(self):
        pass
    
    @abstractmethod
    def authenticate(self) -> bool:
        pass
    
    @abstractmethod
    def post(self, content: str, **kwargs) -> Dict:
        pass
    
    @abstractmethod
    def get_status(self) -> Dict:
        pass


class TwitterTool(BasePlatformTool):
    """Tool for posting to X (Twitter)"""
    
    def _load_credentials(self):
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_secret = os.getenv('TWITTER_ACCESS_SECRET')
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    
    def authenticate(self) -> bool:
        if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            logger.warning("Twitter credentials not configured")
            return False
        try:
            import tweepy
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret
            )
            self.authenticated = True
            return True
        except Exception as e:
            logger.error(f"Twitter auth failed: {e}")
            return False
    
    def post(self, content: str, **kwargs) -> Dict:
        if not self.authenticated and not self.authenticate():
            return {'success': False, 'error': 'Not authenticated'}
        try:
            hashtags = kwargs.get('hashtags', [])
            if hashtags:
                hashtag_str = ' '.join(f'#{tag}' for tag in hashtags[:5])
                if len(content) + len(hashtag_str) + 1 <= 280:
                    content = f"{content} {hashtag_str}"
            response = self.client.create_tweet(text=content)
            return {'success': True, 'tweet_id': response.data['id'], 'platform': 'x'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict:
        return {'platform': 'x', 'authenticated': self.authenticated}


class LinkedInTool(BasePlatformTool):
    """Tool for posting to LinkedIn"""
    
    def _load_credentials(self):
        self.access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        self.person_id = os.getenv('LINKEDIN_PERSON_ID')
    
    def authenticate(self) -> bool:
        if not all([self.access_token, self.person_id]):
            logger.warning("LinkedIn credentials not configured")
            return False
        self.authenticated = True
        return True
    
    def post(self, content: str, **kwargs) -> Dict:
        if not self.authenticated and not self.authenticate():
            return {'success': False, 'error': 'Not authenticated'}
        try:
            import requests
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            post_data = {
                "author": f"urn:li:person:{self.person_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }
            response = requests.post('https://api.linkedin.com/v2/ugcPosts', headers=headers, json=post_data)
            if response.status_code == 201:
                return {'success': True, 'post_id': response.headers.get('x-restli-id'), 'platform': 'linkedin'}
            return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict:
        return {'platform': 'linkedin', 'authenticated': self.authenticated}


class RedditTool(BasePlatformTool):
    """Tool for posting to Reddit"""
    
    def _load_credentials(self):
        self.client_id = os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.username = os.getenv('REDDIT_USERNAME')
        self.password = os.getenv('REDDIT_PASSWORD')
    
    def authenticate(self) -> bool:
        if not all([self.client_id, self.client_secret, self.username, self.password]):
            logger.warning("Reddit credentials not configured")
            return False
        try:
            import praw
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=self.username,
                password=self.password,
                user_agent='MarketingMandy/1.0'
            )
            self.authenticated = True
            return True
        except Exception as e:
            logger.error(f"Reddit auth failed: {e}")
            return False
    
    def post(self, content: str, **kwargs) -> Dict:
        if not self.authenticated and not self.authenticate():
            return {'success': False, 'error': 'Not authenticated'}
        try:
            subreddit = kwargs.get('subreddit', 'test')
            title = kwargs.get('title', content[:100])
            submission = self.reddit.subreddit(subreddit).submit(title=title, selftext=content)
            return {'success': True, 'post_id': submission.id, 'url': submission.url, 'platform': 'reddit'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict:
        return {'platform': 'reddit', 'authenticated': self.authenticated}


class MockPlatformTool(BasePlatformTool):
    """Mock tool for testing without real API calls"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        super().__init__()
    
    def _load_credentials(self):
        pass
    
    def authenticate(self) -> bool:
        self.authenticated = True
        return True
    
    def post(self, content: str, **kwargs) -> Dict:
        logger.info(f"[MOCK] Posting to {self.platform_name}: {content[:50]}...")
        return {
            'success': True,
            'post_id': f'mock_{self.platform_name}_{hash(content) % 10000}',
            'platform': self.platform_name,
            'mock': True
        }
    
    def get_status(self) -> Dict:
        return {'platform': self.platform_name, 'authenticated': True, 'mock': True}


class PlatformManager:
    """Manages all platform tools"""
    
    PLATFORM_MAP = {
        'x': TwitterTool,
        'twitter': TwitterTool,
        'linkedin': LinkedInTool,
        'reddit': RedditTool,
    }
    
    ALL_PLATFORMS = ['x', 'linkedin', 'reddit', 'meta', 'instagram', 'tiktok', 'youtube', 'threads', 'pinterest']
    
    PLATFORM_INFO = {
        'x': {'icon': '𝕏', 'name': 'X (Twitter)', 'max_chars': 280},
        'linkedin': {'icon': '💼', 'name': 'LinkedIn', 'max_chars': 3000},
        'reddit': {'icon': '🔶', 'name': 'Reddit', 'max_chars': 40000},
        'meta': {'icon': '📘', 'name': 'Facebook', 'max_chars': 63206},
        'instagram': {'icon': '📸', 'name': 'Instagram', 'max_chars': 2200},
        'tiktok': {'icon': '🎵', 'name': 'TikTok', 'max_chars': 2200},
        'youtube': {'icon': '📺', 'name': 'YouTube', 'max_chars': 5000},
        'threads': {'icon': '🧵', 'name': 'Threads', 'max_chars': 500},
        'pinterest': {'icon': '📌', 'name': 'Pinterest', 'max_chars': 500},
    }
    
    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock
        self.tools = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        for platform in self.ALL_PLATFORMS:
            if self.use_mock:
                self.tools[platform] = MockPlatformTool(platform)
            elif platform in self.PLATFORM_MAP:
                tool = self.PLATFORM_MAP[platform]()
                if tool.authenticate():
                    self.tools[platform] = tool
                else:
                    self.tools[platform] = MockPlatformTool(platform)
            else:
                self.tools[platform] = MockPlatformTool(platform)
    
    def get_available_platforms(self) -> List[Dict]:
        return [
            {
                'id': pid,
                'name': self.PLATFORM_INFO[pid]['name'],
                'icon': self.PLATFORM_INFO[pid]['icon'],
                'authenticated': tool.authenticated,
                'mock': isinstance(tool, MockPlatformTool)
            }
            for pid, tool in self.tools.items()
        ]
    
    def post(self, platform: str, content: str, **kwargs) -> Dict:
        if platform not in self.tools:
            return {'success': False, 'error': f'Platform {platform} not supported'}
        return self.tools[platform].post(content=content, **kwargs)
