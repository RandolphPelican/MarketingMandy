"""
Platform Tools - Handles posting to various social media platforms
v1.0 Supported: Bluesky, Mastodon, Reddit
Coming Soon: Instagram, LinkedIn, Facebook, TikTok, YouTube, Threads, Pinterest
"""
import os
from typing import Dict, List
from abc import ABC, abstractmethod
import logging
import requests
from datetime import datetime

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


class BlueskyTool(BasePlatformTool):
    """Tool for posting to Bluesky - FREE, instant setup"""
    
    def _load_credentials(self):
        self.handle = os.getenv('BLUESKY_HANDLE')
        self.app_password = os.getenv('BLUESKY_APP_PASSWORD')
        self.access_token = None
        self.did = None
    
    def authenticate(self) -> bool:
        if not all([self.handle, self.app_password]):
            logger.warning("Bluesky credentials not configured")
            return False
        
        try:
            response = requests.post(
                'https://bsky.social/xrpc/com.atproto.server.createSession',
                json={
                    'identifier': self.handle,
                    'password': self.app_password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['accessJwt']
                self.did = data['did']
                self.authenticated = True
                return True
            else:
                logger.error(f"Bluesky auth failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Bluesky auth error: {e}")
            return False
    
    def post(self, content: str, **kwargs) -> Dict:
        if not self.authenticated:
            if not self.authenticate():
                return {'success': False, 'error': 'Not authenticated'}
        
        try:
            record = {
                '$type': 'app.bsky.feed.post',
                'text': content[:300],  # Bluesky limit
                'createdAt': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                'langs': ['en']
            }
            
            response = requests.post(
                'https://bsky.social/xrpc/com.atproto.repo.createRecord',
                headers={'Authorization': f'Bearer {self.access_token}'},
                json={
                    'repo': self.did,
                    'collection': 'app.bsky.feed.post',
                    'record': record
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'post_id': data.get('uri'),
                    'platform': 'bluesky',
                    'url': f"https://bsky.app/profile/{self.handle}/post/{data.get('uri', '').split('/')[-1]}"
                }
            else:
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict:
        return {'platform': 'bluesky', 'authenticated': self.authenticated}


class MastodonTool(BasePlatformTool):
    """Tool for posting to Mastodon - FREE, instant setup"""
    
    def _load_credentials(self):
        self.instance = os.getenv('MASTODON_INSTANCE', 'mastodon.social')
        self.access_token = os.getenv('MASTODON_ACCESS_TOKEN')
    
    def authenticate(self) -> bool:
        if not self.access_token:
            logger.warning("Mastodon credentials not configured")
            return False
        
        try:
            response = requests.get(
                f'https://{self.instance}/api/v1/accounts/verify_credentials',
                headers={'Authorization': f'Bearer {self.access_token}'}
            )
            
            if response.status_code == 200:
                self.authenticated = True
                self.account = response.json()
                return True
            else:
                logger.error(f"Mastodon auth failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Mastodon auth error: {e}")
            return False
    
    def post(self, content: str, **kwargs) -> Dict:
        if not self.authenticated:
            if not self.authenticate():
                return {'success': False, 'error': 'Not authenticated'}
        
        try:
            response = requests.post(
                f'https://{self.instance}/api/v1/statuses',
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                },
                json={
                    'status': content[:500],  # Mastodon default limit
                    'visibility': kwargs.get('visibility', 'public')
                }
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    'success': True,
                    'post_id': data.get('id'),
                    'platform': 'mastodon',
                    'url': data.get('url')
                }
            else:
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict:
        return {'platform': 'mastodon', 'authenticated': self.authenticated}


class RedditTool(BasePlatformTool):
    """Tool for posting to Reddit - FREE for non-commercial"""
    
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
            # Test auth
            _ = self.reddit.user.me()
            self.authenticated = True
            return True
        except Exception as e:
            logger.error(f"Reddit auth failed: {e}")
            return False
    
    def post(self, content: str, **kwargs) -> Dict:
        if not self.authenticated:
            if not self.authenticate():
                return {'success': False, 'error': 'Not authenticated'}
        
        try:
            subreddit = kwargs.get('subreddit', 'test')
            title = kwargs.get('title', content[:100])
            
            submission = self.reddit.subreddit(subreddit).submit(
                title=title,
                selftext=content
            )
            
            return {
                'success': True,
                'post_id': submission.id,
                'url': submission.url,
                'platform': 'reddit'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict:
        return {'platform': 'reddit', 'authenticated': self.authenticated}


class ComingSoonTool(BasePlatformTool):
    """Placeholder for platforms coming soon"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        super().__init__()
    
    def _load_credentials(self):
        pass
    
    def authenticate(self) -> bool:
        return False
    
    def post(self, content: str, **kwargs) -> Dict:
        return {
            'success': False,
            'error': f'{self.platform_name} coming soon! We are awaiting API approval.',
            'platform': self.platform_name,
            'coming_soon': True
        }
    
    def get_status(self) -> Dict:
        return {
            'platform': self.platform_name,
            'authenticated': False,
            'coming_soon': True
        }


class PlatformManager:
    """Manages all platform tools"""
    
    # v1.0 Supported platforms
    SUPPORTED_PLATFORMS = {
        'bluesky': BlueskyTool,
        'mastodon': MastodonTool,
        'reddit': RedditTool,
    }
    
    # Coming soon - awaiting API approval
    COMING_SOON = ['instagram', 'linkedin', 'facebook', 'tiktok', 'youtube', 'threads', 'pinterest']
    
    # Not planned (too expensive)
    # 'x' / 'twitter' - $100/mo minimum
    
    PLATFORM_INFO = {
        'bluesky': {'icon': '🦋', 'name': 'Bluesky', 'max_chars': 300, 'status': 'supported'},
        'mastodon': {'icon': '🐘', 'name': 'Mastodon', 'max_chars': 500, 'status': 'supported'},
        'reddit': {'icon': '🔶', 'name': 'Reddit', 'max_chars': 40000, 'status': 'supported'},
        'instagram': {'icon': '📸', 'name': 'Instagram', 'max_chars': 2200, 'status': 'coming_soon'},
        'linkedin': {'icon': '💼', 'name': 'LinkedIn', 'max_chars': 3000, 'status': 'coming_soon'},
        'facebook': {'icon': '📘', 'name': 'Facebook', 'max_chars': 63206, 'status': 'coming_soon'},
        'tiktok': {'icon': '🎵', 'name': 'TikTok', 'max_chars': 2200, 'status': 'coming_soon'},
        'youtube': {'icon': '📺', 'name': 'YouTube', 'max_chars': 5000, 'status': 'coming_soon'},
        'threads': {'icon': '🧵', 'name': 'Threads', 'max_chars': 500, 'status': 'coming_soon'},
        'pinterest': {'icon': '📌', 'name': 'Pinterest', 'max_chars': 500, 'status': 'coming_soon'},
    }
    
    def __init__(self):
        self.tools = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        # Initialize supported platforms
        for platform, tool_class in self.SUPPORTED_PLATFORMS.items():
            tool = tool_class()
            tool.authenticate()  # Try to auth on init
            self.tools[platform] = tool
        
        # Initialize coming soon placeholders
        for platform in self.COMING_SOON:
            self.tools[platform] = ComingSoonTool(platform)
    
    def get_available_platforms(self) -> List[Dict]:
        result = []
        for pid, info in self.PLATFORM_INFO.items():
            tool = self.tools.get(pid)
            result.append({
                'id': pid,
                'name': info['name'],
                'icon': info['icon'],
                'max_chars': info['max_chars'],
                'status': info['status'],
                'authenticated': tool.authenticated if tool else False,
                'coming_soon': info['status'] == 'coming_soon'
            })
        return result
    
    def post(self, platform: str, content: str, **kwargs) -> Dict:
        if platform not in self.tools:
            return {'success': False, 'error': f'Platform {platform} not supported'}
        return self.tools[platform].post(content=content, **kwargs)
    
    def test_connection(self, platform: str) -> Dict:
        if platform not in self.tools:
            return {'success': False, 'error': 'Platform not found'}
        
        tool = self.tools[platform]
        if isinstance(tool, ComingSoonTool):
            return {'success': False, 'error': 'Coming soon - awaiting API approval', 'coming_soon': True}
        
        success = tool.authenticate()
        return {'success': success, 'platform': platform}
