import httpx
from datetime import datetime
from typing import List, Dict
import hashlib

class HeapClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://heapanalytics.com/api"
    
    async def fetch_events(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch events from Heap API"""
        events = []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            try:
                params = {
                    "from_date": start_date.strftime("%Y-%m-%d"),
                    "to_date": end_date.strftime("%Y-%m-%d")
                }
                
                response = await client.get(
                    f"{self.base_url}/track/events",
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                
                for event_data in data.get("events", []):
                    normalized = {
                        "user_id": self._hash_user_id(event_data.get("user_id", "")),
                        "session_id": event_data.get("session_id"),
                        "event_name": event_data["event"],
                        "timestamp": datetime.fromisoformat(event_data["time"]),
                        "properties": event_data.get("properties", {})
                    }
                    events.append(normalized)
                
            except Exception as e:
                print(f"Heap fetch error: {e}")
        
        return events
    
    def _hash_user_id(self, user_id: str) -> str:
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]