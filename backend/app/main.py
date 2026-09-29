from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.routes import search, deals, export, alerts, nl_search
from app.database.init_db import init_db
import traceback

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS FIRST - before any other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"}
    )

# Include routers
app.include_router(search.router, prefix=f"{settings.API_V1_STR}/search", tags=["search"])
app.include_router(deals.router, prefix=f"{settings.API_V1_STR}/deals", tags=["deals"])
app.include_router(export.router, prefix=f"{settings.API_V1_STR}/export", tags=["export"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(nl_search.router, prefix=f"{settings.API_V1_STR}/nl-search", tags=["nl-search"])

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()
    print(f"🚀 {settings.PROJECT_NAME} API started!")
    print(f"📚 API Documentation: http://localhost:8000/docs")


@app.get("/")
async def root():
    return {
        "message": "Travel Deal Scraper API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
