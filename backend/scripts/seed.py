"""開発用ダミーデータ投入スクリプト（冪等: 既存データはスキップ）"""
import asyncio
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models import (
    User, Company, FinancialData, Document,
    ScreeningRun, ScoringResult, LonglistItem,
)


async def get_or_none(session: AsyncSession, model, **kwargs):
    """条件に一致する最初のレコードを返す。なければ None。"""
    stmt = select(model).filter_by(**kwargs)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def seed(session: AsyncSession) -> None:
    now = datetime.now(timezone.utc)

    # ── Users ──────────────────────────────────────────
    # ── Users（既存ならスキップ）─────────────────────────
    analyst = await get_or_none(session, User, login_email="analyst@example.com")
    if not analyst:
        analyst = User(
            id=uuid.uuid4(),
            login_email="analyst@example.com",
            password_hash=hash_password("password123"),
            role="analyst",
            failed_login_count=0,
            created_at=now,
            updated_at=now,
        )
        session.add(analyst)
        await session.flush()
        print(f"  ✅ users: {analyst.login_email} 作成")
    else:
        print(f"  ⏭️  users: {analyst.login_email} 既存スキップ")

    manager = await get_or_none(session, User, login_email="manager@example.com")
    if not manager:
        manager = User(
            id=uuid.uuid4(),
            login_email="manager@example.com",
            password_hash=hash_password("password123"),
            role="manager",
            failed_login_count=0,
            created_at=now,
            updated_at=now,
        )
        session.add(manager)
        await session.flush()
        print(f"  ✅ users: {manager.login_email} 作成")
    else:
        print(f"  ⏭️  users: {manager.login_email} 既存スキップ")

    # ── Companies（既存ならスキップ）──────────────────────
    co1 = await get_or_none(session, Company, securities_code="1234")
    if not co1:
        co1 = Company(
            id=uuid.uuid4(),
            securities_code="1234",
            name="サンプル不動産株式会社",
            industry="不動産",
            market_cap=150000000000,
            is_universe=True,
            created_at=now,
            updated_at=now,
        )
        session.add(co1)
        await session.flush()
        print(f"  ✅ companies: {co1.name} 作成")
    else:
        print(f"  ⏭️  companies: {co1.name} 既存スキップ")

    co2 = await get_or_none(session, Company, securities_code="5678")
    if not co2:
        co2 = Company(
            id=uuid.uuid4(),
            securities_code="5678",
            name="テスト建設株式会社",
            industry="建設",
            market_cap=80000000000,
            is_universe=True,
            created_at=now,
            updated_at=now,
        )
        session.add(co2)
        await session.flush()
        print(f"  ✅ companies: {co2.name} 作成")
    else:
        print(f"  ⏭️  companies: {co2.name} 既存スキップ")

    companies = [co1, co2]

    # ── FinancialData（既存ならスキップ）─────────────────
    fd1 = await get_or_none(session, FinancialData,
                            company_id=co1.id, as_of_date=date(2025, 3, 31))
    if not fd1:
        fd1 = FinancialData(
            id=uuid.uuid4(), company_id=co1.id, as_of_date=date(2025, 3, 31),
            pbr=0.85, adjusted_pbr=1.20, equity_ratio=45.5,
            unrealized_gain=25000000000, unrealized_gain_ratio=0.167,
            roic=0.032, wacc=0.045, stock_price=1250.0,
        )
        session.add(fd1)

    fd2 = await get_or_none(session, FinancialData,
                            company_id=co2.id, as_of_date=date(2025, 3, 31))
    if not fd2:
        fd2 = FinancialData(
            id=uuid.uuid4(), company_id=co2.id, as_of_date=date(2025, 3, 31),
            pbr=1.10, adjusted_pbr=1.50, equity_ratio=38.2,
            unrealized_gain=12000000000, unrealized_gain_ratio=0.150,
            roic=0.041, wacc=0.048, stock_price=980.0,
        )
        session.add(fd2)

    await session.flush()
    print(f"  ✅ financial_data: 2 件（既存はスキップ）")

    # ── Documents（既存ならスキップ）──────────────────────
    doc = await get_or_none(session, Document,
                            source_url="https://example.com/yuho/1234_2025.pdf")
    if not doc:
        doc = Document(
            id=uuid.uuid4(), company_id=co1.id, document_type="yuho",
            source_url="https://example.com/yuho/1234_2025.pdf",
            disclosed_at=date(2025, 6, 25), created_at=now, updated_at=now,
        )
        session.add(doc)
        await session.flush()
        print(f"  ✅ documents: 1 件 作成")
    else:
        print(f"  ⏭️  documents: 既存スキップ")

    # ── ScreeningRun（is_current=True が既存ならスキップ）──
    run = await get_or_none(session, ScreeningRun, is_current=True)
    if not run:
        run = ScreeningRun(
            id=uuid.uuid4(), triggered_by=analyst.id,
            status="success", is_current=True,
            started_at=now, finished_at=now, duration_ms=3200,
        )
        session.add(run)
        await session.flush()

        scoring_results = [
            ScoringResult(
                id=uuid.uuid4(), screening_run_id=run.id, company_id=co1.id,
                structure_score=72.5, event_score=15.0, total_score=87.5,
                event_boost=1.2, confidence="high",
                ai_judgment="含み益倍率・ROICともに閾値を超過。売却検討の可能性が高い。",
                score_breakdown={"pbr": 20.0, "unrealized_gain": 30.0, "roic": 22.5},
                created_at=now, updated_at=now,
            ),
            ScoringResult(
                id=uuid.uuid4(), screening_run_id=run.id, company_id=co2.id,
                structure_score=55.0, event_score=8.0, total_score=63.0,
                event_boost=1.0, confidence="mid",
                ai_judgment="構造スコアは中程度。追加調査が推奨される。",
                score_breakdown={"pbr": 18.0, "unrealized_gain": 22.0, "roic": 15.0},
                created_at=now, updated_at=now,
            ),
        ]
        session.add_all(scoring_results)
        await session.flush()
        print(f"  ✅ screening_runs: 1 件 / scoring_results: 2 件 作成")

        # ── LonglistItem ───────────────────────────────
        longlist = await get_or_none(session, LonglistItem, company_id=co1.id)
        if not longlist:
            session.add(LonglistItem(
                id=uuid.uuid4(), company_id=co1.id,
                scoring_result_id=scoring_results[0].id,
                status="candidate",
                reason_memo="スコア上位。含み益倍率が高く、アクティビスト圧力も確認済み。",
                created_by=analyst.id, created_at=now,
            ))
            await session.flush()
            print(f"  ✅ longlist_items: 1 件 作成")
    else:
        print(f"  ⏭️  screening_runs / scoring_results / longlist_items: 既存スキップ")

    await session.commit()


async def main():
    print("🌱 シーダー開始...")
    engine = create_async_engine(settings.DATABASE_URL)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        await seed(session)

    await engine.dispose()
    print("✅ シーダー完了")


if __name__ == "__main__":
    asyncio.run(main())
