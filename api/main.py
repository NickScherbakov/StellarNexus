from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import uvicorn
from datetime import datetime, timedelta
import json
import os
from typing import List, Optional
from pydantic import BaseModel

# Import our existing modules
from scripts.main import fetch_top_repos, update_history, generate_chart

app = FastAPI(
    title="StellarNexus API",
    description="AI-Powered GitHub Top Stars Tracker API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Repository(BaseModel):
    name: str
    stars: int
    rank: int
    url: str
    description: Optional[str] = None

class DailyData(BaseModel):
    date: str
    repositories: List[Repository]

class AnalyticsResponse(BaseModel):
    total_repositories: int
    avg_stars: float
    top_gainer: Optional[Repository] = None
    last_updated: str

# Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>StellarNexus - GitHub Top Stars Tracker</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { text-align: center; color: #333; }
            .stats { display: flex; justify-content: space-around; margin: 20px 0; }
            .stat-card { background: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 StellarNexus</h1>
            <p>AI-Powered GitHub Top Stars Tracker</p>
        </div>
        <div class="stats">
            <div class="stat-card">
                <h3>Top Repositories</h3>
                <p id="repo-count">Loading...</p>
            </div>
            <div class="stat-card">
                <h3>Average Stars</h3>
                <p id="avg-stars">Loading...</p>
            </div>
            <div class="stat-card">
                <h3>Last Updated</h3>
                <p id="last-update">Loading...</p>
            </div>
        </div>
        <div id="chart-container">
            <img id="trend-chart" src="/static/stars_trend.png" alt="Star Growth Trend" style="max-width: 100%; height: auto;">
        </div>

        <script>
            async function loadData() {
                try {
                    const response = await fetch('/api/analytics');
                    const data = await response.json();

                    document.getElementById('repo-count').textContent = data.total_repositories;
                    document.getElementById('avg-stars').textContent = data.avg_stars.toLocaleString();
                    document.getElementById('last-update').textContent = new Date(data.last_updated).toLocaleString();
                } catch (error) {
                    console.error('Error loading data:', error);
                }
            }

            loadData();
            setInterval(loadData, 30000); // Refresh every 30 seconds
        </script>
    </body>
    </html>
    """

@app.get("/api/top-repos", response_model=List[Repository])
async def get_top_repositories():
    """Get current top 10 repositories"""
    try:
        # Load latest data from JSON
        if os.path.exists('data/top_repos_history.json'):
            with open('data/top_repos_history.json', 'r') as f:
                history = json.load(f)
                if history:
                    latest_data = history[-1]
                    return latest_data['repositories']
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics", response_model=AnalyticsResponse)
async def get_analytics():
    """Get analytics summary"""
    try:
        if os.path.exists('data/top_repos_history.json'):
            with open('data/top_repos_history.json', 'r') as f:
                history = json.load(f)
                if history:
                    latest_data = history[-1]
                    repos = latest_data['repositories']

                    total_stars = sum(repo['stars'] for repo in repos)
                    avg_stars = total_stars / len(repos) if repos else 0

                    # Find top gainer (simplified - in real app would compare with previous day)
                    top_gainer = max(repos, key=lambda x: x['stars']) if repos else None

                    return AnalyticsResponse(
                        total_repositories=len(repos),
                        avg_stars=round(avg_stars, 2),
                        top_gainer=top_gainer,
                        last_updated=latest_data['date']
                    )

        return AnalyticsResponse(
            total_repositories=0,
            avg_stars=0,
            last_updated=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/refresh-data")
async def refresh_data():
    """Manually trigger data refresh"""
    try:
        print("Starting data refresh...")
        top_repos = fetch_top_repos()
        today_data = update_history(top_repos)
        generate_chart()
        print("Data refresh completed!")
        return {"message": "Data refreshed successfully", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    # Mount static files
    if os.path.exists('docs/assets'):
        app.mount("/static", StaticFiles(directory="docs/assets"), name="static")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )