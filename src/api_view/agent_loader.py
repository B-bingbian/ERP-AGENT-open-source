"""
AgentLoader 单例
持有 agent 实例、数据库连接、create_config、save/get_display_messages
"""
import asyncio
import json
import uuid
from dataclasses import dataclass
from typing import Any, Optional
from datetime import datetime

from ..agent.log_utils import web_logger
from ..agent.schema import ProcurementContext
from .postgres_config import get_postgres_pool
from .database_factory import get_database_store


@dataclass
class AgentSession:
    """一个用户独享的 Agent、稳定沙箱 Proxy 与串行运行锁。"""

    user_id: str
    username: str
    agent: Any
    run_lock: asyncio.Lock


class AgentLoader:
    """Agent 加载器单例 - 管理 Agent 生命周期."""

    _instance: Optional['AgentLoader'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        # ``agent`` 保留为旧代码的兼容字段；新链路一律使用 ``get_session``。
        self.agent = None
        self._checkpointer = None
        self._store = None
        self._mongo_client = None
        self._sessions: dict[str, AgentSession] = {}
        self._resources_lock: asyncio.Lock | None = None
        self._sessions_lock: asyncio.Lock | None = None
        self._session_build_locks: dict[str, asyncio.Lock] = {}
        web_logger.info("AgentLoader initialized")

    async def _ensure_resources(self):
        """Initialize shared Store and Checkpointer."""
        if self._store is not None and self._checkpointer is not None:
            return

        if self._resources_lock is None:
            self._resources_lock = asyncio.Lock()

        async with self._resources_lock:
            if self._store is not None and self._checkpointer is not None:
                return
            await asyncio.to_thread(self._initialize_resources_sync)
            await self._initialize_checkpointer_async()
            web_logger.info("Shared Agent resources initialized")

    def _initialize_resources_sync(self):
        """Blocking store initialization; caller must run in a thread pool."""
        web_logger.info("Initializing shared Agent resources...")
        try:
            self._store = get_database_store()
        except Exception as e:
            web_logger.error(f"Failed to initialize shared Agent resources: {e}")
            raise

    async def _initialize_checkpointer_async(self):
        """Initialize checkpointer based on store type."""
        store = self._store
        if hasattr(store, 'uri') and store.uri.startswith('postgresql://'):
            from psycopg import AsyncConnection
            from psycopg.rows import dict_row
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            conn = await AsyncConnection.connect(
                store.uri, autocommit=True, prepare_threshold=0, row_factory=dict_row
            )
            saver = AsyncPostgresSaver(conn)
            await saver.setup()
            self._checkpointer = saver
            self._pg_conn = conn
            web_logger.info("Using PostgreSQL CheckpointSaver (AsyncPostgresSaver + AsyncConnection)")
        else:
            from langgraph.checkpoint.mongodb import MongoDBSaver
            from pymongo import MongoClient
            mongo_uri = store.uri if hasattr(store, 'uri') else "mongodb://localhost:27017"
            mongo_client = MongoClient(mongo_uri)
            self._checkpointer = MongoDBSaver(mongo_client)
            self._mongo_client = mongo_client
            web_logger.info("Using MongoDB CheckpointSaver")

    async def initialize(self, user_id: str | None = None, username: str = "用户"):
        """兼容旧调用：初始化共享资源，可选地预创建一个用户会话。"""
        await self._ensure_resources()
        if user_id is not None:
            await self.get_session(user_id, username)

    async def get_session(self, user_id: str, username: str = "用户") -> AgentSession:
        """获取用户独享的 Agent 会话，避免不同用户共享 Sandbox/中间件状态。"""
        await self._ensure_resources()

        if self._sessions_lock is None:
            self._sessions_lock = asyncio.Lock()
        async with self._sessions_lock:
            existing = self._sessions.get(user_id)
            if existing is not None:
                return existing
            build_lock = self._session_build_locks.setdefault(user_id, asyncio.Lock())

        async with build_lock:
            async with self._sessions_lock:
                existing = self._sessions.get(user_id)
                if existing is not None:
                    return existing

            agent = await asyncio.to_thread(
                self._build_agent_for_user, user_id, username
            )
            session = AgentSession(
                user_id=user_id,
                username=username,
                agent=agent,
                run_lock=asyncio.Lock(),
            )
            async with self._sessions_lock:
                self._sessions[user_id] = session
                self._session_build_locks.pop(user_id, None)
                # 兼容仍读取该字段的调试脚本。
                if user_id == "default_user":
                    self.agent = agent
            web_logger.info(f"Agent session ready for user: {user_id}")
            return session

    def _build_agent_for_user(self, user_id: str, username: str):
        """在线程池中构建 _build_agent_for_userAgent；其中包含 Docker/Mongo 同步 I/O。"""
        from ..agent.main_agent import create_main_agent

        context = ProcurementContext(user_id=user_id, username=username)
        return create_main_agent(
            user_context=context,
            checkpointer=self._checkpointer,
            store=self._store,
        )

    @property
    def store(self):
        """供请求级工具上下文读取的共享 Store。"""
        return self._store

    def create_config(self, thread_id: str, user_id: str = "default_user") -> dict:
        """创建 LangGraph 运行配置"""
        return {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
            }
        }

    def generate_thread_id(self) -> str:
        """生成新的会话线程ID"""
        return str(uuid.uuid4())

    async def save_display_messages(self, thread_id: str, messages: list):
        """Save frontend display messages to PostgreSQL."""
        pool = await get_postgres_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO display_messages (thread_id, messages, updated_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (thread_id)
                DO UPDATE SET messages = EXCLUDED.messages, updated_at = NOW()
                """,
                thread_id,
                json.dumps(messages, ensure_ascii=False),
            )

    async def get_display_messages(self, thread_id: str) -> list:
        """Get frontend display messages from PostgreSQL."""
        pool = await get_postgres_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT messages FROM display_messages WHERE thread_id = $1", thread_id
            )
            if row is None:
                return []
            messages = row["messages"]
            if isinstance(messages, str):
                return json.loads(messages)
            return messages if messages else []

    async def save_conversation(self, thread_id: str, user_id: str, title: str = "新对话"):
        """Save/update conversation record in PostgreSQL."""
        pool = await get_postgres_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO conversations (thread_id, user_id, title, created_at, updated_at)
                VALUES ($1, $2, $3, NOW(), NOW())
                ON CONFLICT (thread_id)
                DO UPDATE SET user_id = EXCLUDED.user_id, title = EXCLUDED.title, updated_at = NOW()
                """,
                thread_id, user_id, title,
            )

    async def get_conversations(self, user_id: str) -> list:
        """Get user conversation list from PostgreSQL."""
        pool = await get_postgres_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT thread_id, title, created_at, updated_at
                FROM conversations
                WHERE user_id = $1
                ORDER BY updated_at DESC
                """,
                user_id,
            )
            conversations = []
            for row in rows:
                conversations.append({
                    "thread_id": row["thread_id"],
                    "title": row["title"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                })
            return conversations

    async def get_conversation_user_id(self, thread_id: str) -> str | None:
        """Get conversation owner user_id from PostgreSQL."""
        pool = await get_postgres_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT user_id FROM conversations WHERE thread_id = $1", thread_id
            )
            return row["user_id"] if row else None

    async def delete_conversation(self, thread_id: str):
        """Delete conversation from PostgreSQL."""
        pool = await get_postgres_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM conversations WHERE thread_id = $1", thread_id)
            await conn.execute("DELETE FROM display_messages WHERE thread_id = $1", thread_id)
            await conn.execute("DELETE FROM harness_traces WHERE thread_id = $1", thread_id)

    async def save_harness_trace(self, thread_id: str, trace: list):
        """Save harness phase trace to PostgreSQL."""
        pool = await get_postgres_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO harness_traces (thread_id, trace, updated_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (thread_id)
                DO UPDATE SET trace = EXCLUDED.trace, updated_at = NOW()
                """,
                thread_id,
                json.dumps(trace, ensure_ascii=False),
            )


# 全局单例
agent_loader = AgentLoader()
