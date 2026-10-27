"""
PostgreSQL 持久化 Store（替代 InMemoryStore）

基于 LangGraph BaseStore 接口，使用 PostgreSQL 作为后端存储。
支持用户偏好、技能持久化等跨会话数据的持久化存储。

设计：
- 继承 BaseStore，实现 put/get/search/delete 接口
- 使用 asyncpg 异步客户端
- 数据格式：每个 namespace + key 组合为一条 PostgreSQL 记录
- 支持 TTL（可选）
"""
import json
import asyncpg
from typing import Any, Optional, Sequence
from datetime import datetime
from uuid import uuid4

from langgraph.store.base import BaseStore, Item, Op

from ..agent.log_utils import web_logger


class PostgreSQLStore(BaseStore):
    """
    PostgreSQL 持久化 Store

    数据存储格式：
    {
        "id": UUID,
        "namespace": ["tuple", "of", "strings"],
        "key": "item_key",
        "value": { ... },  # 任意 JSON-serializable 值
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    """

    def __init__(
        self,
        uri: str = "postgresql://postgres:postgres@localhost:5432/erp_agent",
        db_name: str = "erp_agent",
        table_name: str = "langgraph_store",
    ):
        super().__init__()
        self.uri = uri
        self.db_name = db_name
        self.table_name = table_name
        self._pool: Optional[asyncpg.Pool] = None
        self._initialized = False

    async def _init_db(self):
        """初始化数据库表"""
        if self._initialized:
            return

        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.uri)

        async with self._pool.acquire() as conn:
            # 创建表
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    namespace JSONB NOT NULL,
                    key TEXT NOT NULL,
                    value JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            # 创建索引
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_namespace_key
                ON {self.table_name} (namespace, key)
            """)

            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_updated_at
                ON {self.table_name} (updated_at)
            """)

        self._initialized = True
        web_logger.info(f"PostgreSQLStore initialized: {self.db_name}.{self.table_name}")

    async def _get_db_connection(self):
        """获取数据库连接"""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.uri)
        return self._pool

    def _namespace_key(self, namespace: tuple[str, ...], key: str) -> str:
        """生成唯一键"""
        ns_str = "::".join(namespace)
        return f"{ns_str}::{key}"

    async def _get_item_by_id(self, item_id: str) -> Optional[Item]:
        """通过ID获取项目"""
        await self._init_db()

        async with self._pool.acquire() as conn:
            doc = await conn.fetchrow(
                f"SELECT * FROM {self.table_name} WHERE id = $1",
                item_id
            )
            if doc is None:
                return None
            return self._doc_to_item(dict(doc))

    def _doc_to_item(self, doc: dict) -> Item:
        """将 PostgreSQL 文档转为 Item"""
        namespace = tuple(doc.get("namespace", []))
        return Item(
            namespace=namespace,
            key=doc.get("key", ""),
            value=doc.get("value"),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
        )

    async def _namespace_prefix_query(self, prefix: tuple[str, ...]) -> str:
        """构造 namespace 前缀查询"""
        conditions = []
        for index, value in enumerate(prefix):
            conditions.append(f"namespace[$1] = ${index + 2}")
        return " AND ".join(conditions)

    # ============================================================
    # 核心 CRUD 接口
    # ============================================================

    async def get(self, namespace: tuple[str, ...], key: str) -> Optional[Item]:
        """获取单个存储项"""
        await self._init_db()

        ns_query = await self._namespace_prefix_query(namespace)
        async with self._pool.acquire() as conn:
            doc = await conn.fetchrow(
                f"""
                SELECT * FROM {self.table_name}
                WHERE {ns_query} AND key = $1
                ORDER BY updated_at DESC
                """,
                key,
                *namespace
            )
            if doc is None:
                return None
            return self._doc_to_item(dict(doc))

    async def put(self, namespace: tuple[str, ...], key: str, value: Any) -> Item:
        """写入/更新存储项"""
        await self._init_db()

        now = datetime.now().isoformat()
        serialized = self._serialize_value(value)

        ns_query = await self._namespace_prefix_query(namespace)

        async with self._pool.acquire() as conn:
            # 尝试更新现有记录
            result = await conn.fetchrow(
                f"""
                UPDATE {self.table_name}
                SET value = $1, updated_at = $2
                WHERE {ns_query} AND key = $3
                RETURNING id
                """,
                serialized,
                now,
                key,
                *namespace
            )

            if result:
                # 更新成功，获取完整记录
                return await self.get(namespace, key)
            else:
                # 插入新记录
                await conn.execute(
                    f"""
                    INSERT INTO {self.table_name} (namespace, key, value, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    list(namespace),
                    key,
                    serialized,
                    now,
                    now
                )

                return Item(
                    namespace=namespace,
                    key=key,
                    value=value,
                    created_at=now,
                    updated_at=now,
                )

    async def search(
        self,
        namespace_prefix: tuple[str, ...],
        *,
        query: Optional[str] = None,
        filter: Optional[dict] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Item]:
        """搜索存储项（按 namespace 前缀匹配）"""
        await self._init_db()

        conditions = [await self._namespace_prefix_query(namespace_prefix)]

        if filter:
            # 简单值过滤
            for k, v in filter.items():
                conditions.append(f"value->>'{k}' = ${len(conditions) + 1}")

        where_clause = " AND ".join(conditions)

        params = list(namespace_prefix)
        param_count = len(namespace_prefix)

        if filter:
            for v in filter.values():
                params.append(v)
                param_count += 1

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT * FROM {self.table_name}
                WHERE {where_clause}
                ORDER BY updated_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
                """,
                *params,
                limit,
                offset
            )

            return [self._doc_to_item(dict(row)) for row in rows]

    async def delete(self, namespace: tuple[str, ...], key: str) -> None:
        """删除存储项"""
        await self._init_db()

        ns_query = await self._namespace_prefix_query(namespace)
        async with self._pool.acquire() as conn:
            await conn.execute(
                f"""
                DELETE FROM {self.table_name}
                WHERE {ns_query} AND key = $1
                """,
                key,
                *namespace
            )

    async def list_namespaces(
        self,
        *,
        prefix: Optional[tuple[str, ...]] = None,
        max_depth: Optional[int] = None,
    ) -> list[tuple[str, ...]]:
        """列出所有 namespace"""
        await self._init_db()

        conditions = []
        params = []

        if prefix:
            ns_query = await self._namespace_prefix_query(prefix)
            conditions.append(ns_query)
            params.extend(list(prefix))

        where_clause = " AND ".join(conditions) if conditions else ""

        async with self._pool.acquire() as conn:
            if where_clause:
                rows = await conn.fetch(
                    f"""
                    SELECT DISTINCT namespace FROM {self.table_name}
                    WHERE {where_clause}
                    """,
                    *params
                )
            else:
                rows = await conn.fetch(
                    f"""
                    SELECT DISTINCT namespace FROM {self.table_name}
                    """
                )

            namespaces = []
            for row in rows:
                ns = tuple(row.get("namespace", []))
                if max_depth:
                    ns = ns[:max_depth]
                namespaces.append(ns)

            return sorted(namespaces)

    # ============================================================
    # 批量接口
    # ============================================================

    async def batch(self, ops: Sequence[Op]) -> list[Any]:
        """批量操作"""
        results = []
        for op in ops:
            if op[0] == "get":
                results.append(await self.get(op[1], op[2]))
            elif op[0] == "put":
                results.append(await self.put(op[1], op[2], op[3]))
            elif op[0] == "search":
                results.append(await self.search(op[1], **op[2] if len(op) > 2 else {}))
            elif op[0] == "delete":
                await self.delete(op[1], op[2])
                results.append(None)
            else:
                results.append(None)
        return results

    async def abatch(self, ops: Sequence[Op]) -> list[Any]:
        """异步批量操作（BaseStore 抽象方法实现）"""
        return await self.batch(ops)

    # ============================================================
    # 内部工具
    # ============================================================

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """序列化值（确保 JSON 兼容）"""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        if isinstance(value, dict):
            return value
        if isinstance(value, (list, tuple)):
            return list(value)
        # 其他类型转为字符串
        return str(value)

    async def close(self):
        """关闭连接池"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._initialized = False