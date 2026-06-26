from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints import (
    auth,
    companies,
    dashboard,
    events,
    files,
    kpi,
    longlist,
    screenings,
    users,
)
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.dependencies import get_db
from app.repositories.user_repository import UserRepository

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(screenings.router)
app.include_router(companies.router)
app.include_router(files.router)
app.include_router(longlist.router)
app.include_router(kpi.router)
app.include_router(events.router)


@app.get("/health", tags=["Health"])
async def alb_health_check():
    """ALB 用ヘルスチェック（認証不要）"""
    return {"status": "healthy"}


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/api/v1/db-test", tags=["Health"])
async def db_test():
    """DB 接続テスト"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return {"status": "Database connected", "result": result.scalar()}
    except Exception as e:
        return {"status": "Database connection failed", "error": str(e)}


@app.get("/api/v1/db-schema-test", tags=["Health"])
async def db_schema_test(session: AsyncSession = Depends(get_db)):
    """スキーマ確認テスト：users テーブルが存在するか"""
    try:
        repo = UserRepository(session)
        users = await repo.list(limit=1)
        return {"status": "Schema OK", "users_table_exists": True, "count": len(users)}
    except Exception as e:
        return {"status": "Schema error", "error": str(e)}


@app.get("/")
async def root():
    return {"message": "Property Sale Screening API"}
