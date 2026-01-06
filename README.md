# CXM Product Intelligence MVP

Automated product analytics intelligence system that turns fragmented data into actionable PM insights.

## Features

- Real-time data ingestion from Mixpanel, Amplitude, PostHog, Heap, GA4
- Automated metric computation (DAU/WAU/MAU, retention, feature adoption, funnels)
- Anomaly detection and regression alerts
- LLM-powered explanations and natural language queries
- API-first architecture

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost/cxm_intelligence
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
```

Run:

```bash
python main.py
```

### Frontend

```bash
cd frontend
npm install
```

Create `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Run:

```bash
npm run dev
```

## Environment Variables

### Backend

- `DATABASE_URL` - PostgreSQL connection string
- `LLM_PROVIDER` - `openai`, `anthropic`, or `ollama`
- `OPENAI_API_KEY` - OpenAI API key (if using OpenAI)
- `OPENAI_MODEL` - Model name (default: gpt-4)
- `ANTHROPIC_API_KEY` - Anthropic API key (if using Anthropic)
- `ANTHROPIC_MODEL` - Model name (default: claude-3-sonnet-20240229)
- `OLLAMA_BASE_URL` - Ollama endpoint (default: http://localhost:11434)
- `OLLAMA_MODEL` - Ollama model (default: llama2)

### Frontend

- `NEXT_PUBLIC_API_URL` - Backend API URL

## Using Different LLMs

To switch LLM providers, update `.env`:

**OpenAI:**
```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
```

**Anthropic:**
```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

**Ollama (Local):**
```
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

## API Endpoints

- `POST /api/ingestion/sync` - Sync data from sources
- `GET /api/metrics/dau` - Daily active users
- `GET /api/metrics/retention` - Retention metrics
- `GET /api/insights/` - Get all insights
- `POST /api/query/ask` - Ask natural language questions

## Data Ingestion

Example sync request:

```json
{
  "configs": [
    {
      "source": "mixpanel",
      "api_key": "your_key",
      "api_secret": "your_secret",
      "lookback_days": 7
    }
  ]
}
```

## License

MIT
