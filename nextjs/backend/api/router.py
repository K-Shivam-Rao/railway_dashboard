"""Router — aggregates all sub-routers under /api/v1."""
from fastapi import APIRouter
from backend.api.metrics import router as metrics_router
from backend.api.stations import router as stations_router
from backend.api.incidents import router as incidents_router
from backend.api.network import router as network_router
from backend.api.financial import router as financial_router
from backend.api.customers import router as customers_router
from backend.api.analytics import router as analytics_router
from backend.api.budget import router as budget_router
from backend.api.reports import router as reports_router
from backend.api.visualization import router as visualization_router

api_router = APIRouter(prefix="/api/v1")

for _r in (metrics_router, stations_router, incidents_router, network_router,
           financial_router, customers_router, analytics_router,
           budget_router, reports_router, visualization_router):
    api_router.include_router(_r)
