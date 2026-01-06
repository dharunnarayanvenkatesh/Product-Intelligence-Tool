import os
import json
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: str = None) -> str:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
    
    async def generate(self, prompt: str, system: str = None) -> str:
        try:
            import openai
            openai.api_key = self.api_key
            
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model = model
    
    async def generate(self, prompt: str, system: str = None) -> str:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            message = await client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system if system else "",
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Error: {str(e)}"

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
    
    async def generate(self, prompt: str, system: str = None) -> str:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                full_prompt = f"{system}\n\n{prompt}" if system else prompt
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": full_prompt, "stream": False}
                )
                return response.json()["response"]
        except Exception as e:
            return f"Error: {str(e)}"

class LLMClient:
    def __init__(self):
        provider_type = os.getenv("LLM_PROVIDER", "openai")
        
        if provider_type == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            model = os.getenv("OPENAI_MODEL", "gpt-4")
            self.provider = OpenAIProvider(api_key, model)
        elif provider_type == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
            self.provider = AnthropicProvider(api_key, model)
        elif provider_type == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model = os.getenv("OLLAMA_MODEL", "llama2")
            self.provider = OllamaProvider(base_url, model)
        else:
            raise ValueError(f"Unknown LLM provider: {provider_type}")
    
    async def explain_insight(self, detection: dict) -> str:
        """Convert detection data into PM-readable explanation"""
        system = """You are a product intelligence assistant. Convert technical metrics and detections 
        into clear, actionable explanations for Product Managers. Focus on:
        1. What happened
        2. Why it matters
        3. What action to take"""
        
        prompt = f"""Explain this insight:
        
Type: {detection['type']}
Severity: {detection['severity']}
Title: {detection['title']}
Data: {json.dumps(detection['data'], indent=2)}

Provide a clear 2-3 sentence explanation suitable for a PM."""
        
        return await self.provider.generate(prompt, system)
    
    async def query(self, question: str, context: dict) -> str:
        """Answer natural language questions about metrics"""
        system = """You are a product analytics expert. Answer questions about product metrics 
        using the provided context. Be specific and data-driven."""
        
        prompt = f"""Question: {question}

Available Context:
Metrics: {json.dumps(context['metrics'][:20], indent=2)}
Insights: {json.dumps(context['insights'][:10], indent=2)}

Provide a clear, data-driven answer."""
        
        return await self.provider.generate(prompt, system)
    
    async def analyze_metric(self, context: dict) -> str:
        """Deep dive analysis of a specific metric"""
        system = """You are a product analytics expert. Analyze metric trends and provide 
        actionable insights."""
        
        prompt = f"""Analyze this metric:

Metric: {context['metric_name']}
History: {json.dumps(context['history'][:15], indent=2)}
Related Insights: {json.dumps(context['insights'], indent=2)}

Provide:
1. Trend analysis
2. Key observations
3. Recommended actions"""
        
        return await self.provider.generate(prompt, system)