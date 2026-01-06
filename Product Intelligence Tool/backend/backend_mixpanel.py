import httpx
import base64
from datetime import datetime
from typing import List, Dict

class MixpanelClient:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://mixpanel.com/api/2.0"
        
        # Create auth header
        auth_str = f"{api_secret}:"
        auth_bytes = auth_str.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        self.auth_header = f"Basic {auth_b64}"
    
    async def fetch_events(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch events from Mixpanel Export API"""
        events = []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            params = {
                "from_date": start_date.strftime("%Y-%m-%d"),
                "to_date": end_date.strftime("%Y-%m-%d")
            }
            
            try:
                response = await client.get(
                    f"{self.base_url}/export",
                    params=params,
                    headers={"Authorization": self.auth_header}
                )
                response.raise_for_status()
                
                # Mixpanel returns JSONL (one JSON object per line)
                for line in response.text.strip().split('\n'):
                    if not line:
                        continue
                    
                    import json
                    event_data = json.loads(line)
                    
                    # Normalize to our schema
                    normalized = {
                        "user_id": self._hash_user_id(event_data["properties"].get("distinct_id")),
                        "session_id": event_data["properties"].get("$session_id"),
                        "event_name": event_data["event"],
                        "timestamp": datetime.fromtimestamp(event_data["properties"]["time"]),
                        "properties": {
                            k: v for k, v in event_data["properties"].items()
                            if not k.startswith("$") and k not in ["time", "distinct_id"]
                        }
                    }
                    events.append(normalized)
                
            except Exception as e:
                print(f"Mixpanel fetch error: {e}")
        
        return events
    
    def _hash_user_id(self, user_id: str) -> str:
        """Hash user ID for privacy"""
        import hashlib
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]