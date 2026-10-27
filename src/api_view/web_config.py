"""
PostgreSQL 连接配置
AsyncPG 连接.
"""
import os
from .postgres_config import get_db, close_postgres_pool
from ..agent.env_utils import get_env

POSTGRES_URI = get_env("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/erp_agent")
POSTGRES_DB_NAME = get_env("POSTGRES_DB_NAME", "erp_agent")
