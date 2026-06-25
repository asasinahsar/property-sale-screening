"""デモ用テストデータ投入スクリプト.

使い方:
    cd backend && uv run python scripts/seed_demo_data.py
"""

import asyncio
import uuid
from datetime import date, datetime

from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal
from app.models.company import Company, Document, FinancialData, QualitativeSignal


DEMO_COMPANIES = [
    {
        "securities_code": "1234",
        "name": "東京不動産ホールディングス",
        "industry": "不動産",
        "market_cap": 15000.0,
        "pbr": 0.6,
        "adjusted_pbr": 0.7,
        "equity_ratio": 0.65,
        "unrealized_gain": 800.0,
        "unrealized_gain_ratio": 0.53,
        "roic": 0.10,
        "wacc": 0.05,
    },
    {
        "securities_code": "2345",
        "name": "大阪商業地開発",
        "industry": "不動産",
        "market_cap": 8000.0,
        "pbr": 0.9,
        "adjusted_pbr": 1.0,
        "equity_ratio": 0.55,
        "unrealized_gain": 400.0,
        "unrealized_gain_ratio": 0.50,
        "roic": 0.07,
        "wacc": 0.06,
    },
    {
        "securities_code": "3456",
        "name": "名古屋倉庫リート",
        "industry": "倉庫・物流",
        "market_cap": 5000.0,
        "pbr": 1.2,
        "adjusted_pbr": 1.3,
        "equity_ratio": 0.40,
        "unrealized_gain": 200.0,
        "unrealized_gain_ratio": 0.40,
        "roic": 0.04,
        "wacc": 0.07,
    },
    {
        "securities_code": "4567",
        "name": "関西小売チェーン",
        "industry": "小売",
        "market_cap": 3000.0,
        "pbr": 0.5,
        "adjusted_pbr": 0.6,
        "equity_ratio": 0.70,
        "unrealized_gain": 600.0,
        "unrealized_gain_ratio": 0.20,
        "roic": 0.12,
        "wacc": 0.04,
    },
    {
        "securities_code": "5678",
        "name": "九州製造業",
        "industry": "製造",
        "market_cap": 12000.0,
        "pbr": 0.8,
        "adjusted_pbr": 0.9,
        "equity_ratio": 0.60,
        "unrealized_gain": 1200.0,
        "unrealized_gain_ratio": 0.10,
        "roic": 0.09,
        "wacc": 0.06,
    },
]

DEMO_SIGNALS = [
    # 東京不動産ホールディングス: アクティビスト提案あり
    {
        "company_code": "1234",
        "signal_type": "activist_proposal",
        "stance": "support",
        "strength": 0.85,
        "quote_text": "当社に対し、保有不動産の売却および株主還元強化を求める株主提案が提出されました。",
        "source_page": 12,
    },
    {
        "company_code": "1234",
        "signal_type": "capital_efficiency_target",
        "stance": "support",
        "strength": 0.70,
        "quote_text": "2025年度末までにROE 10%達成を目指し、不動産ポートフォリオの最適化を推進します。",
        "source_page": 5,
    },
    # 大阪商業地開発: 売却示唆あり
    {
        "company_code": "2345",
        "signal_type": "sale_suggestion",
        "stance": "support",
        "strength": 0.60,
        "quote_text": "遊休資産の活用として、一部物件の売却を検討していることを開示します。",
        "source_page": 8,
    },
    # 名古屋倉庫リート: 反証シグナル
    {
        "company_code": "3456",
        "signal_type": "sale_suggestion",
        "stance": "counter",
        "strength": 0.50,
        "quote_text": "当社は保有物件を長期保有方針とし、売却の予定はありません。",
        "source_page": 3,
    },
]


async def seed():
    async with AsyncSessionLocal() as session:
        # 既存データ確認
        existing = await session.execute(
            select(Company).where(
                Company.securities_code.in_([c["securities_code"] for c in DEMO_COMPANIES])
            )
        )
        existing_codes = {c.securities_code for c in existing.scalars().all()}

        company_id_map: dict[str, uuid.UUID] = {}
        now = datetime.utcnow()
        as_of = date(2024, 3, 31)

        # Company + FinancialData を投入
        for data in DEMO_COMPANIES:
            code = data["securities_code"]
            if code in existing_codes:
                # 既存: IDだけ取得
                result = await session.execute(
                    select(Company).where(Company.securities_code == code)
                )
                company = result.scalar_one()
                company_id_map[code] = company.id
                print(f"  SKIP (already exists): {data['name']} ({code})")
                continue

            company_id = uuid.uuid4()
            company = Company(
                id=company_id,
                securities_code=code,
                name=data["name"],
                industry=data["industry"],
                market_cap=data["market_cap"],
                is_universe=True,
                created_at=now,
                updated_at=now,
            )
            session.add(company)

            fd = FinancialData(
                id=uuid.uuid4(),
                company_id=company_id,
                as_of_date=as_of,
                pbr=data["pbr"],
                adjusted_pbr=data["adjusted_pbr"],
                equity_ratio=data["equity_ratio"],
                unrealized_gain=data["unrealized_gain"],
                unrealized_gain_ratio=data["unrealized_gain_ratio"],
                roic=data["roic"],
                wacc=data["wacc"],
            )
            session.add(fd)
            company_id_map[code] = company_id
            print(f"  INSERT: {data['name']} ({code})")

        await session.commit()

        # QualitativeSignal を投入（ダミー Document が必要）
        for sig_data in DEMO_SIGNALS:
            code = sig_data["company_code"]
            company_id = company_id_map.get(code)
            if company_id is None:
                continue

            # ダミー Document を作成（なければ）
            doc_result = await session.execute(
                select(Document).where(Document.company_id == company_id).limit(1)
            )
            doc = doc_result.scalar_one_or_none()
            if doc is None:
                doc = Document(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    document_type="yuho",
                    source_url=f"https://example.com/{code}/yuho.pdf",
                    disclosed_at=as_of,
                    created_at=now,
                    updated_at=now,
                )
                session.add(doc)
                await session.flush()

            # シグナルが重複しないよう確認
            existing_sig = await session.execute(
                select(QualitativeSignal).where(
                    QualitativeSignal.company_id == company_id,
                    QualitativeSignal.quote_text == sig_data["quote_text"],
                )
            )
            if existing_sig.scalar_one_or_none() is not None:
                print(f"  SKIP signal (already exists): {code} / {sig_data['signal_type']}")
                continue

            sig = QualitativeSignal(
                id=uuid.uuid4(),
                company_id=company_id,
                document_id=doc.id,
                signal_type=sig_data["signal_type"],
                stance=sig_data["stance"],
                strength=sig_data["strength"],
                recency=as_of,
                source_page=sig_data["source_page"],
                quote_text=sig_data["quote_text"],
                created_at=now,
            )
            session.add(sig)
            print(f"  INSERT signal: {code} / {sig_data['signal_type']} ({sig_data['stance']})")

        await session.commit()
        print("\n✅ シードデータ投入完了")


if __name__ == "__main__":
    asyncio.run(seed())
