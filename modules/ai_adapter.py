"""
AI服务适配器 - 支持多种AI服务的统一接口
"""
import requests
from typing import Optional
from loguru import logger
from abc import ABC, abstractmethod


class AIServiceAdapter(ABC):
    """AI服务适配器基类"""
    
    @abstractmethod
    def call_api(self, prompt: str) -> Optional[str]:
        """调用API获取回答"""
        pass


class BaiduAdapter(AIServiceAdapter):
    """百度千帆适配器"""
    
    def __init__(self, config: dict):
        self.base_url = config['base_url']
        self.api_key = config['api_key']
        self.model = config['model']
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
    
    def call_api(self, prompt: str) -> Optional[str]:
        """调用百度API"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content']
                else:
                    logger.warning(f"API调用失败 (尝试 {attempt+1}/{self.max_retries}): {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"API调用异常 (尝试 {attempt+1}/{self.max_retries}): {e}")
        
        return None


class OpenAIAdapter(AIServiceAdapter):
    """OpenAI适配器 (也支持兼容OpenAI格式的API)"""
    
    def __init__(self, config: dict):
        self.api_key = config['api_key']
        self.model = config['model']
        self.base_url = config.get('base_url', 'https://api.openai.com/v1')
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
    
    def call_api(self, prompt: str) -> Optional[str]:
        """调用OpenAI API"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content']
                else:
                    logger.warning(f"OpenAI API调用失败 (尝试 {attempt+1}/{self.max_retries}): {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"OpenAI API调用异常 (尝试 {attempt+1}/{self.max_retries}): {e}")
        
        return None


class ClaudeAdapter(AIServiceAdapter):
    """Anthropic Claude适配器"""
    
    def __init__(self, config: dict):
        self.api_key = config['api_key']
        self.model = config['model']
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
    
    def call_api(self, prompt: str) -> Optional[str]:
        """调用Claude API"""
        url = "https://api.anthropic.com/v1/messages"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['content'][0]['text']
                else:
                    logger.warning(f"Claude API调用失败 (尝试 {attempt+1}/{self.max_retries}): {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Claude API调用异常 (尝试 {attempt+1}/{self.max_retries}): {e}")
        
        return None


class OllamaAdapter(AIServiceAdapter):
    """Ollama本地LLM适配器"""
    
    def __init__(self, config: dict):
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.model = config['model']
        self.timeout = config.get('timeout', 60)
        self.max_retries = config.get('max_retries', 3)
    
    def call_api(self, prompt: str) -> Optional[str]:
        """调用Ollama API"""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('response', '')
                else:
                    logger.warning(f"Ollama API调用失败 (尝试 {attempt+1}/{self.max_retries}): {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Ollama API调用异常 (尝试 {attempt+1}/{self.max_retries}): {e}")
        
        return None


def create_ai_adapter(config: dict) -> AIServiceAdapter:
    """
    根据配置创建AI适配器
    
    Args:
        config: 完整的配置字典
        
    Returns:
        AIServiceAdapter: AI服务适配器实例
    """
    # 优先使用新的ai_service配置
    if 'ai_service' in config:
        provider = config['ai_service'].get('provider', 'baidu')
        
        if provider == 'baidu':
            return BaiduAdapter(config['ai_service']['baidu'])
        elif provider == 'openai':
            return OpenAIAdapter(config['ai_service']['openai'])
        elif provider == 'claude':
            return ClaudeAdapter(config['ai_service']['claude'])
        elif provider == 'ollama':
            return OllamaAdapter(config['ai_service']['ollama'])
        else:
            logger.warning(f"未知的AI服务提供商: {provider}, 回退到百度")
            return BaiduAdapter(config['ai_service']['baidu'])
    
    # 向后兼容: 使用旧的deepseek配置
    elif 'deepseek' in config:
        logger.info("使用旧的deepseek配置 (建议迁移到ai_service)")
        return BaiduAdapter(config['deepseek'])
    
    else:
        raise ValueError("配置文件中未找到ai_service或deepseek配置")
