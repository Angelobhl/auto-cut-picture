#!/usr/bin/env python3
"""
数据库初始化脚本

用法:
    python -m scripts.init_db           # 初始化数据库
    python -m scripts.init_db --reset   # 重置数据库（删除并重建）
    python -m scripts.init_db --help    # 显示帮助信息
"""
import asyncio
import argparse
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import init_db, close_db
from app.db.models import Base
from app.config.settings import settings


async def init_database(reset: bool = False):
    """Initialize or reset the database."""
    print(f"Storage path: {settings.STORAGE_PATH}")
    print(f"Database path: {settings.database_path}")

    # Ensure storage directory exists
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)

    if reset:
        # Import here to avoid circular imports
        from sqlalchemy.ext.asyncio import create_async_engine

        db_url = f"sqlite+aiosqlite:///{settings.database_path}"
        engine = create_async_engine(db_url, echo=True)

        print("Dropping all tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        await engine.dispose()
        print("All tables dropped.")

    # Initialize database (creates tables)
    print("Initializing database...")
    await init_db(settings.STORAGE_PATH)
    print(f"Database initialized at: {settings.database_path}")

    await close_db()


def main():
    parser = argparse.ArgumentParser(
        description="初始化 SQLite 数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m scripts.init_db           初始化数据库（创建表）
  python -m scripts.init_db --reset   重置数据库（删除并重建所有表）
        """
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="重置数据库（删除所有表并重建）"
    )
    args = parser.parse_args()

    print("=" * 50)
    print("Auto Cut Picture - 数据库初始化")
    print("=" * 50)

    try:
        asyncio.run(init_database(args.reset))
        print("\n✅ 数据库初始化成功!")
    except Exception as e:
        print(f"\n❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()