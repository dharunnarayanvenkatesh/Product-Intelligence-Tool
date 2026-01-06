from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

from database import get_db, Event, SyncState
from integrations.mixpanel import MixpanelClient
from integrations.amplitude import AmplitudeClient
from integrations.posthog import PostHogClient
from integrations.heap import HeapClient
from integrations.ga4 import GA4Client

router = APIRouter()

class SourceConfig(BaseModel):
    source: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    project_id: Optional[str] = None
    workspace_id: Optional[str] = None
    lookback_days: int = 7

class IngestRequest(BaseModel):
    configs: List[SourceConfig]

async def ingest_from_source(config: SourceConfig, db: AsyncSession):
    try:
        client = None
        if config.source == "mixpanel":
            client = MixpanelClient(config.api_key, config.api_secret)
        elif config.source == "amplitude":
            client = AmplitudeClient(config.api_key, config.api_secret)
        elif config.source == "posthog":
            client = PostHogClient(config.api_key, config.project_id)
        elif config.source == "heap":
            client = HeapClient(config.api_key)
        elif config.source == "ga4":
            client = GA4Client(config.api_key, config.project_id)
        else:
            return {"error": f"Unknown source: {config.source}"}
        
        # Get last sync
        result = await db.execute(select(SyncState).where(SyncState.source == config.source))
        sync_state = result.scalar_one_or_none()
        
        if sync_state and sync_state.last_sync:
            start_date = sync_state.last_sync
        else:
            start_date = datetime.utcnow() - timedelta(days=config.lookback_days)
        
        end_date = datetime.utcnow()
        
        # Fetch events
        events = await client.fetch_events(start_date, end_date)
        
        # Normalize and insert
        for event_data in events:
            event = Event(
                user_id=event_data.get("user_id"),
                session_id=event_data.get("session_id"),
                event_name=event_data.get("event_name"),
                timestamp=event_data.get("timestamp"),
                source=config.source,
                properties=event_data.get("properties", {})
            )
            db.add(event)
        
        # Update sync state
        if sync_state:
            sync_state.last_sync = end_date
            sync_state.status = "success"
        else:
            sync_state = SyncState(
                source=config.source,
                last_sync=end_date,
                status="success"
            )
            db.add(sync_state)
        
        await db.commit()
        return {"status": "success", "events_ingested": len(events)}
    
    except Exception as e:
        # Update sync state with error
        if sync_state:
            sync_state.status = "error"
            sync_state.metadata = {"error": str(e)}
            await db.commit()
        return {"status": "error", "message": str(e)}

@router.post("/sync")
async def sync_sources(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    results = []
    for config in request.configs:
        result = await ingest_from_source(config, db)
        results.append({"source": config.source, "result": result})
    
    return {"results": results}

@router.get("/status")
async def get_sync_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SyncState))
    states = result.scalars().all()
    return {"sync_states": [
        {
            "source": s.source,
            "last_sync": s.last_sync.isoformat() if s.last_sync else None,
            "status": s.status,
            "metadata": s.metadata
        }
        for s in states
    ]}