"""スクリーニング実行・スコアリング結果 Repository."""

import uuid
from datetime import datetime

from sqlalchemy import select, update

from app.models.screening import ScreeningRun, ScoringResult
from app.repositories.base import BaseRepository


class ScreeningRunRepository(BaseRepository[ScreeningRun]):
    """ScreeningRun の CRUD + 特殊操作."""

    def __init__(self, session):
        super().__init__(session, ScreeningRun)

    async def create_run(
        self,
        triggered_by_user_id: uuid.UUID | None = None,
    ) -> ScreeningRun:
        """新規スクリーニング実行を作成（status=running, is_current=False）."""
        run = ScreeningRun(
            triggered_by=triggered_by_user_id,
            status="running",
            is_current=False,
            started_at=datetime.utcnow(),
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def set_current(self, run_id: uuid.UUID) -> ScreeningRun | None:
        """原子的に is_current を更新。

        1. 全ての既存 run の is_current を False に
        2. 指定 run_id の is_current を True、status を success に更新
        （1つのトランザクション内で実行）
        """
        # 全 run の is_current を False に
        await self.session.execute(update(ScreeningRun).values(is_current=False))
        # 指定 run を is_current=True, status=success, finished_at=now() に
        await self.session.execute(
            update(ScreeningRun)
            .where(ScreeningRun.id == run_id)
            .values(
                is_current=True,
                status="success",
                finished_at=datetime.utcnow(),
            )
        )
        await self.session.commit()
        return await self.get(run_id)

    async def mark_failed(self, run_id: uuid.UUID) -> ScreeningRun | None:
        """指定 run の status を failed に更新."""
        await self.session.execute(
            update(ScreeningRun)
            .where(ScreeningRun.id == run_id)
            .values(status="failed", finished_at=datetime.utcnow())
        )
        await self.session.commit()
        return await self.get(run_id)

    async def get_current_run(self) -> ScreeningRun | None:
        """is_current=True の run を取得."""
        stmt = select(ScreeningRun).where(ScreeningRun.is_current.is_(True))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ScoringResultRepository(BaseRepository[ScoringResult]):
    """ScoringResult の CRUD + 特殊操作."""

    def __init__(self, session):
        super().__init__(session, ScoringResult)

    async def bulk_create(self, results: list[ScoringResult]) -> list[ScoringResult]:
        """複数の ScoringResult を一括 INSERT（commit 1回）."""
        for result in results:
            self.session.add(result)
        await self.session.commit()
        for result in results:
            await self.session.refresh(result)
        return results

    async def get_by_run_id(self, run_id: uuid.UUID) -> list[ScoringResult]:
        """run_id でフィルタして ScoringResult 一覧を取得."""
        stmt = select(ScoringResult).where(ScoringResult.screening_run_id == run_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
