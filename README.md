# Executive Portfolio Health Dashboard

A Streamlit dashboard that consolidates status, metrics, risks, and roadmap data across multiple technology programs into a single view for leadership. It is built to answer the questions asked in a portfolio review: which programs are on track, what is at risk, and what is the business impact.

> All programs, people, and numbers are synthetic and exist only to demonstrate the dashboard.

## Features

- **KPI strip:** program count, share on track, annual value, hours saved per month, and open high risks
- **Program health table:** RAG (red/amber/green) status, health score, progress, budget used, schedule slip, value, and adoption
- **Progress vs. budget chart:** spots programs spending faster than they deliver
- **Roadmap:** milestone timeline per program with a "today" marker
- **Risk and dependency register:** sorted by severity, showing which programs depend on others
- **Executive summary:** one click generates a short leadership summary. With an OpenAI API key it is AI-generated; without one, a template summary built from the data is shown
- **Service line filter** in the sidebar

## How the health score works

Each program starts at 100 and loses points for:

- spending ahead of progress (1.2 points per percentage point that budget used exceeds % complete)
- schedule slip (1 point per day)
- open high-severity risks (6 points each)

Scores of 80+ are Green, 60 to 79 Amber, and below 60 Red. The weights are simple on purpose and are easy to change in `data.py`.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

To enable AI-generated summaries:

```bash
export OPENAI_API_KEY="your-key"
```

## Files

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit dashboard |
| `data.py` | Synthetic data and health scoring |
| `requirements.txt` | Python dependencies |

## Tools

Python, Streamlit, pandas, Altair, OpenAI API
