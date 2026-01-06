from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
from datetime import datetime
from typing import List, Dict
import hashlib
import os

class GA4Client:
    def __init__(self, credentials_path: str, property_id: str):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        self.client = BetaAnalyticsDataClient()
        self.property_id = property_id
    
    async def fetch_events(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch events from GA4 Data API"""
        events = []
        
        try:
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[DateRange(
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d")
                )],
                dimensions=[
                    Dimension(name="eventName"),
                    Dimension(name="userId"),
                    Dimension(name="sessionId"),
                    Dimension(name="date")
                ],
                metrics=[Metric(name="eventCount")]
            )
            
            response = self.client.run_report(request)
            
            for row in response.rows:
                event_name = row.dimension_values[0].value
                user_id = row.dimension_values[1].value
                session_id = row.dimension_values[2].value
                date_str = row.dimension_values[3].value
                
                # Parse date (format: YYYYMMDD)
                event_date = datetime.strptime(date_str, "%Y%m%d")
                
                normalized = {
                    "user_id": self._hash_user_id(user_id) if user_id != "(not set)" else "anonymous",
                    "session_id": session_id if session_id != "(not set)" else None,
                    "event_name": event_name,
                    "timestamp": event_date,
                    "properties": {}
                }
                events.append(normalized)
                
        except Exception as e:
            print(f"GA4 fetch error: {e}")
        
        return events
    
    def _hash_user_id(self, user_id: str) -> str:
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]