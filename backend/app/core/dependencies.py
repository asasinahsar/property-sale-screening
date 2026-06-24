from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """DB セッション取得（Slice 0-2 で実装）"""
    raise NotImplementedError("Slice 0-2 で実装します")
