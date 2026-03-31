#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库状态检测工具
功能：检测当前数据库状态，判断是否需要爬取
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db_connect import get_current_period, has_data_in_period, get_db_stats


def check_status():
    """检测当前数据库状态"""
    print("\n" + "=" * 60)
    print("📊 社交媒体热点词分析平台 - 数据库状态检测")
    print("=" * 60)
    
    now = datetime.now()
    print(f"├─ 当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    current_period = get_current_period()
    period_name = "上午 (00:00-11:59)" if current_period == 'morning' else "下午 (12:00-23:59)"
    print(f"├─ 当前时段：{period_name}")
    
    # 检查上午数据
    has_morning_common, morning_common_time = has_data_in_period('common', 'morning')
    has_morning_tech, morning_tech_time = has_data_in_period('tech', 'morning')
    
    # 检查下午数据
    has_afternoon_common, afternoon_common_time = has_data_in_period('common', 'afternoon')
    has_afternoon_tech, afternoon_tech_time = has_data_in_period('tech', 'afternoon')
    
    print("├─ 上午数据状态：")
    print(f"│   ├─ 综合类：{'✅ 已存在' if has_morning_common else '❌ 不存在'} ({morning_common_time or ''})")
    print(f"│   └─ 科技类：{'✅ 已存在' if has_morning_tech else '❌ 不存在'} ({morning_tech_time or ''})")
    
    print("├─ 下午数据状态：")
    print(f"│   ├─ 综合类：{'✅ 已存在' if has_afternoon_common else '❌ 不存在'} ({afternoon_common_time or ''})")
    print(f"│   └─ 科技类：{'✅ 已存在' if has_afternoon_tech else '❌ 不存在'} ({afternoon_tech_time or ''})")
    
    stats = get_db_stats()
    print("├─ 数据库总计：")
    print(f"│   ├─ 综合类：{stats['common']['count']} 条")
    print(f"│   └─ 科技类：{stats['tech']['count']} 条")
    
    print("└─ 建议操作：")
    if current_period == 'morning':
        if not has_morning_common or not has_morning_tech:
            print("    ⚠️  上午数据不完整，建议手动爬取：python src/crawler.py --force")
        else:
            print("    ✅ 上午数据已完整，等待 12:00 进入下午时段")
    else:
        if not has_afternoon_common or not has_afternoon_tech:
            print("    ⚠️  下午数据不完整，建议手动爬取：python src/crawler.py --force")
        else:
            print("    ✅ 下午数据已完整，等待明天 00:00 进入上午时段")
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    check_status()