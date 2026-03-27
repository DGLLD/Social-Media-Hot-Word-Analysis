#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目 - 数据库连接模块

功能：
1. SQLite 数据库连接管理
2. 数据库初始化
3. 数据入库（综合类/科技类）
4. 数据查询
5. 半天数据检查与删除

作者: 毕业实习项目组
创建时间: 2026-03-27
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any

# ================================
# 日志配置
# ================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M'
)
logger = logging.getLogger(__name__)

# ================================
# 数据库路径配置
# ================================
# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / 'database' / 'hotspot.db'
SCHEMA_PATH = PROJECT_ROOT / 'database' / 'schema.sql'

# 确保 database 目录存在
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection():
    """
    获取 SQLite 数据库连接

    Returns:
        sqlite3.Connection: 数据库连接对象
    """
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row  # 支持字典式访问
    # 性能优化配置
    conn.execute("PRAGMA journal_mode = WAL")      # WAL 模式，支持读写并发
    conn.execute("PRAGMA synchronous = NORMAL")    # 性能与安全平衡
    conn.execute("PRAGMA cache_size = 10000")      # 增加缓存
    return conn


def init_database():
    """
    初始化数据库
    如果数据库不存在，则根据 schema.sql 创建表结构
    """
    if not SCHEMA_PATH.exists():
        logger.error(f"❌ schema.sql 文件不存在: {SCHEMA_PATH}")
        return False

    conn = None
    try:
        conn = get_connection()
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
        logger.info(f"✅ 数据库初始化完成: {DB_PATH}")
        return True
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败：{e}")
        return False
    finally:
        if conn:
            conn.close()


def get_current_period():
    """
    获取当前时段

    Returns:
        str: 'morning' (0-11 点) 或 'afternoon' (12-23 点)
    """
    hour = datetime.now().hour
    return 'morning' if hour < 12 else 'afternoon'


def get_period_time_range(period: str, date=None):
    """
    获取指定半天的时间范围

    Args:
        period: 'morning' 或 'afternoon'
        date: 日期 (datetime.date)，默认今天

    Returns:
        tuple: (start_time, end_time) 字符串格式
    """
    if date is None:
        date = datetime.now().date()

    if period == 'morning':
        start = datetime(date.year, date.month, date.day, 0, 0, 0)
        end = datetime(date.year, date.month, date.day, 11, 59, 59)
    else:  # afternoon
        start = datetime(date.year, date.month, date.day, 12, 0, 0)
        end = datetime(date.year, date.month, date.day, 23, 59, 59)

    return (
        start.strftime('%Y-%m-%d %H:%M:%S'),
        end.strftime('%Y-%m-%d %H:%M:%S')
    )


def has_data_in_period(category: str, period: str, date=None) -> Tuple[bool, Optional[str]]:
    """
    检查指定半天是否已有数据

    Args:
        category: 'common' 或 'tech'
        period: 'morning' 或 'afternoon'
        date: 日期，默认今天

    Returns:
        tuple: (是否有数据，最后更新时间)
    """
    table_name = 'hot_rank_common' if category == 'common' else 'hot_rank_tech'
    start_time, end_time = get_period_time_range(period, date)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = f"""
            SELECT crawl_time FROM {table_name} 
            WHERE crawl_time >= ? AND crawl_time <= ?
            ORDER BY crawl_time DESC LIMIT 1
        """
        cursor.execute(sql, (start_time, end_time))
        row = cursor.fetchone()

        if row:
            logger.info(f"✅ [{category}] {period} 已有数据：{row['crawl_time']}")
            return True, row['crawl_time']
        else:
            logger.info(f"❌ [{category}] {period} 无数据")
            return False, None

    except Exception as e:
        logger.error(f"❌ 检查数据失败：{e}")
        return False, None
    finally:
        if conn:
            conn.close()


def delete_period_data(category: str, period: str, date=None) -> int:
    """
    删除指定半天的数据（覆盖用）

    Args:
        category: 'common' 或 'tech'
        period: 'morning' 或 'afternoon'
        date: 日期，默认今天

    Returns:
        int: 删除的条数
    """
    table_name = 'hot_rank_common' if category == 'common' else 'hot_rank_tech'
    start_time, end_time = get_period_time_range(period, date)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = f"""
            DELETE FROM {table_name} 
            WHERE crawl_time >= ? AND crawl_time <= ?
        """
        cursor.execute(sql, (start_time, end_time))
        deleted_count = cursor.rowcount
        conn.commit()

        logger.info(f"🗑️  [{category}] 删除 {period} 数据 {deleted_count} 条")
        return deleted_count

    except Exception as e:
        logger.error(f"❌ 删除数据失败：{e}")
        if conn:
            conn.rollback()
        return 0
    finally:
        if conn:
            conn.close()


def save_hot_rank(category: str, normalized_score: float, title: str, url: str, crawl_time: str = None) -> bool:
    """
    通用入库函数

    Args:
        category: 'common' 或 'tech'
        normalized_score: 归一化序号 (0-1 之间)
        title: 标题
        url: 链接
        crawl_time: 入库时间（可选）

    Returns:
        bool: 是否成功
    """
    table_name = 'hot_rank_common' if category == 'common' else 'hot_rank_tech'

    if crawl_time is None:
        crawl_time = datetime.now().strftime('%Y-%m-%d %H:00:00')

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = f"INSERT INTO {table_name} (normalized_score, title, url, crawl_time) VALUES (?, ?, ?, ?)"
        cursor.execute(sql, (normalized_score, title, url, crawl_time))
        conn.commit()

        logger.info(f"✅ [{category}] 入库成功：{title[:30]}...")
        return True

    except Exception as e:
        logger.error(f"❌ [{category}] 入库失败：{e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def save_hot_rank_common(normalized_score: float, title: str, url: str, crawl_time: str = None) -> bool:
    """保存综合类热榜数据"""
    return save_hot_rank('common', normalized_score, title, url, crawl_time)


def save_hot_rank_tech(normalized_score: float, title: str, url: str, crawl_time: str = None) -> bool:
    """保存科技类热榜数据"""
    return save_hot_rank('tech', normalized_score, title, url, crawl_time)


def get_latest_data(category: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    获取最新的热榜数据

    Args:
        category: 'common' 或 'tech'
        limit: 返回条数

    Returns:
        list: 数据列表，每条包含 normalized_score, title, url, crawl_time
    """
    table_name = 'hot_rank_common' if category == 'common' else 'hot_rank_tech'

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = f"""
            SELECT normalized_score, title, url, crawl_time 
            FROM {table_name} 
            ORDER BY crawl_time DESC, normalized_score ASC 
            LIMIT ?
        """
        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"❌ 获取数据失败：{e}")
        return []
    finally:
        if conn:
            conn.close()


def get_db_stats() -> Dict[str, Any]:
    """
    获取数据库统计信息

    Returns:
        dict: 包含综合类和科技类的数据统计
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 综合类统计
        cursor.execute("SELECT COUNT(*) FROM hot_rank_common")
        common_count = cursor.fetchone()[0]

        # 科技类统计
        cursor.execute("SELECT COUNT(*) FROM hot_rank_tech")
        tech_count = cursor.fetchone()[0]

        # 最后入库时间
        cursor.execute("SELECT MAX(crawl_time) FROM hot_rank_common")
        common_last = cursor.fetchone()[0]

        cursor.execute("SELECT MAX(crawl_time) FROM hot_rank_tech")
        tech_last = cursor.fetchone()[0]

        return {
            'common': {'count': common_count, 'last_time': common_last},
            'tech': {'count': tech_count, 'last_time': tech_last}
        }

    except Exception as e:
        logger.error(f"❌ 获取统计信息失败：{e}")
        return {'common': {'count': 0, 'last_time': None}, 'tech': {'count': 0, 'last_time': None}}
    finally:
        if conn:
            conn.close()


# ================================
# 测试代码
# ================================
if __name__ == '__main__':
    print("=" * 60)
    print("数据库连接模块测试")
    print("=" * 60)

    # 1. 初始化数据库
    print("\n1. 初始化数据库...")
    init_database()

    # 2. 检查当前时段
    print(f"\n2. 当前时段: {get_current_period()}")

    # 3. 检查上午数据
    print("\n3. 检查上午数据...")
    has_common, common_time = has_data_in_period('common', 'morning')
    print(f"   综合类: {'有' if has_common else '无'} {common_time if common_time else ''}")

    has_tech, tech_time = has_data_in_period('tech', 'morning')
    print(f"   科技类: {'有' if has_tech else '无'} {tech_time if tech_time else ''}")

    # 4. 获取数据库统计
    print("\n4. 数据库统计:")
    stats = get_db_stats()
    print(f"   综合类: {stats['common']['count']} 条, 最后入库: {stats['common']['last_time']}")
    print(f"   科技类: {stats['tech']['count']} 条, 最后入库: {stats['tech']['last_time']}")

    # 5. 获取最新数据
    print("\n5. 最新数据 (前5条):")
    latest = get_latest_data('common', 5)
    for i, item in enumerate(latest, 1):
        print(f"   {i}. {item['title'][:40]}...")

    print("\n✅ 数据库模块测试完成")