#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目 - 定时自动爬取脚本

功能：
1. 每天 10:00 和 16:00 自动执行
2. 检查当前半天是否已有数据，避免重复爬取
3. 调用爬虫主程序

配置 Windows 定时任务：
    schtasks /create /tn "HotspotCrawl" /tr "python D:\project\src\auto_crawl.py" /sc daily /st 10:00
    schtasks /create /tn "HotspotCrawl2" /tr "python D:\project\src\auto_crawl.py" /sc daily /st 16:00

作者: 毕业实习项目组
创建时间: 2026-03-27
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ================================
# 导入模块
# ================================
try:
    from src.db_connect import (
        get_current_period,
        has_data_in_period,
        init_database
    )
    from src.crawler import main as crawl_main
except ImportError:
    from db_connect import (
        get_current_period,
        has_data_in_period,
        init_database
    )
    from crawler import main as crawl_main

# ================================
# 日志配置
# ================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M'
)
logger = logging.getLogger(__name__)


def should_crawl() -> tuple:
    """
    判断是否需要爬取

    Returns:
        tuple: (是否爬取，原因)
    """
    current_period = get_current_period()
    period_name = "上午" if current_period == 'morning' else "下午"

    # 检查当前半天数据
    has_common, common_time = has_data_in_period('common', current_period)
    has_tech, tech_time = has_data_in_period('tech', current_period)

    if has_common and has_tech:
        return False, f"{period_name}数据已完整，跳过爬取"
    else:
        missing = []
        if not has_common:
            missing.append("综合类")
        if not has_tech:
            missing.append("科技类")
        return True, f"{period_name}数据缺失 ({', '.join(missing)})，执行爬取"


def auto_crawl():
    """自动爬取主函数"""
    logger.info("=" * 60)
    logger.info("🤖 自动爬取任务启动")
    logger.info(f"📅 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    try:
        # 初始化数据库
        init_database()

        # 判断是否需要爬取
        need_crawl, reason = should_crawl()
        logger.info(f"📊 状态检测：{reason}")

        if need_crawl:
            logger.info("🚀 开始爬取...")
            # 调用爬虫（force=False，自动任务不覆盖）
            crawl_main(force=False)
            logger.info("✅ 自动爬取完成")
        else:
            logger.info("⏭️ 跳过本次爬取")

    except Exception as e:
        logger.error(f"❌ 自动爬取失败：{e}")
        raise

    logger.info("=" * 60)


if __name__ == "__main__":
    auto_crawl()