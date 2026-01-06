import httpx
from datetime import datetime
from typing import List, Dict
import hashlib

class AmplitudeClient:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://amplitude.com/api/2"
    
    async def fetch_events(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch events from Amplitude Export API"""
        events = []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            params = {
                "start": start_date.strftime("%Y%m%dT%H"),
                "end": end_date.strftime("%Y%m%dT%H")
            }
            
            try:
                response = await client.get(
                    f"{self.base_url}/export",
                    params=params,
                    auth=(self.api_key, self.api_secret)
                )
                response.raise_for_status()
                
                # Amplitude returns ZIP with JSONL
                import zipfile
                import io
                import json
                
                with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                    for filename in zf.namelist():
                        with zf.open(filename) as f:
                            for line in f:
                                if not line.strip():
                                    continue
                                
                                event_data = json.loads(line)
                                
                                normalized = {
                                    "user_id": self._hash_user_id(event_data.get("user_id", "")),
                                    "session_id": str(event_data.get("session_id")),
                                    "event_name": event_data["event_type"],
                                    "timestamp": datetime.fromtimestamp(event_data["event_time"] / 1000),
                                    "properties": event_data.get("event_properties", {})
                                }
                                events.append(normalized)
                
            except Exception as e:
                print(f"Amplitude fetch error: {e}")
        
        return events
    
    def _hash_user_id(self, user_id: str) -> str:
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]