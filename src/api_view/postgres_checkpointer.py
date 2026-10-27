"""
PostgreSQL Checkpoint 实现
基于 LangGraph BaseCheckpointSaver 接口
"""
import uuid
from typing import Any, Dict, Optional, Tuple, Union
from datetime import datetime

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import CheckpointTuple


class PostgresCheckpointSaver(BaseCheckpointSaver):
    """
    PostgreSQL 实现的 Checkpoint Saver

    存储格式：
    {
        "thread_id": UUID,
        "checkpoint_id": UUID,
        "checkpoint": JSON,
        "writes": JSON,
        "parent_checkpoint_id": UUID,
        "met/adata": JSON
    }
    """

    def __init__(self, connection_string: str, table_name: str = "checkpoints"):
        super().__init__()
        self.connection_string = connection_string
        self.table_name = table_name
        self._pool = None

    async def get_pool(self):
        if self._pool is None:
            import asyncpg
            self._pool = await asyncpg.create_pool(self.connection_string)
        return self._pool

    async def aget(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """获取 Checkpoint"""
        thread_id = config.get("thread_id")
        checkpoint_id = config.get("checkpoint_id")

        if not thread_id:
            return None

        pool = await self.get_pool()
        async with pool.acquire() as conn:
            if checkpoint_id:
                # 通过 checkpoint_id 获取
                row = await conn.fetchrow(
                    f"SELECT * FROM {self.table_name} WHERE thread_id = $1 AND checkpoint_id = $2",
                    thread_id,
                    checkpoint_id
                )
            else:
                # 获取最新的 checkpoint
                row = await conn.fetchrow(
                    f"SELECT * FROM {self.table_name} WHERE thread_id = $1 ORDER BY created_at DESC LIMIT 1",
                    thread_id
                )

            if not row:
                return None

            return CheckpointTuple(
                config={
                    "thread_id": str(row["thread_id"]),
                    "checkpoint_id": str(row["checkpoint_id"])
                },
                checkpoint=row["checkpoint"],
                metadata=row["metadata"],
                parent_config={
                    "thread_id": str(row["thread_id"]),
                    "checkpoint_id": str(row["parent_checkpoint_id"])
                } if row["parent_checkpoint_id"] else None,
                pending_writes=row["writes"]
            )

    async def aput(
        self,
        config: Dict[str, Any],
        checkpoint: Dict[str, Any],
        writes: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """保存 Checkpoint"""
        thread_id = config["thread_id"]
        checkpoint_id = config["checkpoint_id"]
        parent_id = config.get("parent_checkpoint_id")

        pool = await self.get_pool()
        async with pool.acquire() as conn:
            # 插入或更新 checkpoint
            await conn.execute(
                f"""
                INSERT INTO {self.table_name}
                (thread_id, checkpoint_id, checkpoint, writes, parent_checkpoint_id, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                ON CONFLICT (thread_id, checkpoint_id)
                DO UPDATE SET
                    checkpoint = EXCLUDED.checkpoint,
                    writes = EXCLUDED.writes,
                    metadata = EXCLUDED.metadata,
                    created_at = NOW()
                """,
                thread_id,
                checkpoint_id,
                checkpoint,
                writes,
                parent_id if parent_id else None,
                metadata or {}
            )

        return {
            "thread_id": config["thread_id"],
            "checkpoint_id": config["checkpoint_id"]
        }

    async def alist(
        self,
        config: Dict[str, Any],
        *,
        limit: Optional[int] = None,
        before: Optional[Dict[str, Any]] = None,
    ) -> list[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """列出 Checkpoint"""
        thread_id = config["thread_id"]
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            query = f"SELECT * FROM {self.table_name} WHERE thread_id = $1"
            params = [thread_id]
            param_count = 1

            if before:
                query += " AND (created_at < $2 OR (created_at = $2 AND checkpoint_id < $3))"
                params.extend([before["created_at"], before["checkpoint_id"]])
                param_count += 2

            query += " ORDER BY created_at DESC"
            if limit:
                query += f" LIMIT ${param_count + 1}"
                params.append(limit)
                param_count += 1

            rows = await conn.fetch(query, *params)

            return [
                (
                    {
                        "thread_id": str(row["thread_id"]),
                        "checkpoint_id": str(row["checkpoint_id"])
                    },
                    row["metadata"]
                )
                for row in rows
            ]

    async def aclear(self, config: Dict[str, Any]) -> None:
        """清除 Checkpoint"""
        thread_id = config["thread_id"]
        checkpoint_id = config.get("checkpoint_id")

        pool = await self.get_pool()
        async with pool.acquire() as conn:
            if checkpoint_id:
                await conn.execute(
                    f"DELETE FROM {self.table_name} WHERE thread_id = $1 AND checkpoint_id = $2",
                    thread_id,
                    checkpoint_id
                )
            else:
                await conn.execute(
                    f"DELETE FROM {self.table_name} WHERE thread_id = $1",
                    thread_id
                )

    async def setup_table(self):
        """初始化检查点表"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    thread_id UUID NOT NULL,
                    checkpoint_id UUID NOT NULL,
                    checkpoint JSONB NOT NULL,
                    writes JSONB,
                    parent_checkpoint_id UUID,
                    metadata JSONB DEFAULT '{{}}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    PRIMARY KEY (thread_id, checkpoint_id)
                )
            """)
            # 创建索引
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_thread_created
                ON {self.table_name} (thread_id, created_at)
            """)