import httpx
from datetime import datetime
from typing import List, Dict
import hashlib

class PostHogClient:
    def __init__(self, api_key: str, project_id: str, host: str = "https://app.posthog.com"):
        self.api_key = api_key
        self.project_id = project_id
        self.host = host
    
    async def fetch_events(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch events from PostHog API"""
        events = []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            try:
                # PostHog uses query API
                query = {
                    "kind": "EventsQuery",
                    "select": ["*"],
                    "after": start_date.isoformat(),
                    "before": end_date.isoformat()
                }
                
                response = await client.post(
                    f"{self.host}/api/projects/{self.project_id}/query",
                    json=query,
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                
                for event_data in data.get("results", []):
                    normalized = {
                        "user_id": self._hash_user_id(event_data.get("distinct_id", "")),
                        "session_id": event_data.get("properties", {}).get("$session_id"),
                        "event_name": event_data["event"],
                        "timestamp": datetime.fromisoformat(event_data["timestamp"].replace("Z", "+00:00")),
                        "properties": {
                            k: v for k, v in event_data.get("properties", {}).items()
                            if not k.startswith("$")
                        }
                    }
                    events.append(normalized)
                
            except Exception as e:
                print(f"PostHog fetch error: {e}")
        
        return events
    
    def _hash_user_id(self, user_id: str) -> str:
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]