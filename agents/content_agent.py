"""
Content Generation Agent - Uses LangChain to generate platform-specific posts
"""
import os
from typing import Dict, List
from pydantic import BaseModel, Field


class GeneratedPost(BaseModel):
    """Schema for generated social media post"""
    content: str = Field(description="The main post content")
    hashtags: List[str] = Field(description="Relevant hashtags")
    media_suggestions: List[str] = Field(description="Suggestions for images/videos")
    engagement_hooks: List[str] = Field(description="Call-to-action suggestions")


class ContentAgent:
    """Agent responsible for generating marketing content across platforms"""
    
    PLATFORM_CONFIGS = {
        'x': {
            'max_chars': 280,
            'style': 'concise, punchy, thread-friendly',
            'tone': 'casual, witty, conversational'
        },
        'linkedin': {
            'max_chars': 3000,
            'style': 'professional, thought-leadership, storytelling',
            'tone': 'professional, insightful, value-driven'
        },
        'reddit': {
            'max_chars': 40000,
            'style': 'authentic, community-focused, non-promotional',
            'tone': 'genuine, helpful, NOT salesy'
        },
        'meta': {
            'max_chars': 2200,
            'style': 'visual-first, engaging, shareable',
            'tone': 'friendly, relatable'
        },
        'instagram': {
            'max_chars': 2200,
            'style': 'visual-first, aesthetic, hashtag-rich',
            'tone': 'aspirational, authentic'
        },
        'tiktok': {
            'max_chars': 2200,
            'style': 'trend-aware, hook-driven, entertaining',
            'tone': 'casual, fun, gen-z friendly'
        },
        'youtube': {
            'max_chars': 5000,
            'style': 'SEO-optimized, descriptive',
            'tone': 'informative, engaging'
        },
        'threads': {
            'max_chars': 500,
            'style': 'conversational, authentic',
            'tone': 'casual, genuine'
        },
        'pinterest': {
            'max_chars': 500,
            'style': 'descriptive, keyword-rich',
            'tone': 'inspiring, actionable'
        }
    }
    
    def __init__(self, model_provider: str = "anthropic"):
        self.model_provider = model_provider
        self.llm = None
        self._init_model()
    
    def _init_model(self):
        """Initialize the LLM based on provider"""
        try:
            if self.model_provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                self.llm = ChatAnthropic(
                    model="claude-sonnet-4-20250514",
                    temperature=0.8,
                    max_tokens=2000
                )
            else:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model="gpt-4-turbo-preview",
                    temperature=0.8,
                    max_tokens=2000
                )
        except Exception as e:
            print(f"Warning: Could not initialize LLM: {e}")
            self.llm = None
    
    def generate_post(
        self,
        platform: str,
        product_name: str,
        product_description: str,
        target_audience: str = "",
        style: str = "professional"
    ) -> Dict:
        """Generate a marketing post for a specific platform"""
        
        config = self.PLATFORM_CONFIGS.get(platform, self.PLATFORM_CONFIGS['x'])
        
        if not self.llm:
            # Fallback mock response
            return {
                'content': f"Check out {product_name}! {product_description[:100]}...",
                'hashtags': ['marketing', product_name.lower().replace(' ', '')],
                'media_suggestions': ['Product photo', 'Logo'],
                'engagement_hooks': ['Learn more!', 'Link in bio']
            }
        
        prompt = f"""You are Marketing Mandy, an expert social media marketer.
Create a {platform} post for:

Product: {product_name}
Description: {product_description}
Audience: {target_audience or 'general'}
Style: {style}

Platform requirements:
- Max {config['max_chars']} characters
- Style: {config['style']}
- Tone: {config['tone']}

Return ONLY a JSON object with these keys:
- content: the post text
- hashtags: array of hashtags (without #)
- media_suggestions: array of image/video ideas
- engagement_hooks: array of CTA ideas

Make it authentic, not salesy AI slop."""

        try:
            response = self.llm.invoke(prompt)
            import json
            # Try to parse JSON from response
            text = response.content
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
        except Exception as e:
            print(f"Generation error: {e}")
        
        # Fallback
        return {
            'content': f"Check out {product_name}! {product_description[:100]}",
            'hashtags': ['marketing'],
            'media_suggestions': ['Product photo'],
            'engagement_hooks': ['Learn more!']
        }
    
    def adapt_content(self, original: str, source: str, target: str) -> str:
        """Adapt content from one platform to another"""
        target_config = self.PLATFORM_CONFIGS.get(target, {})
        max_chars = target_config.get('max_chars', 280)
        
        if len(original) <= max_chars:
            return original
        return original[:max_chars-3] + "..."
