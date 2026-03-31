#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库备份/恢复/清空工具
功能：
1. 备份数据库到 dbcheck/
2. 清空数据库
3. 从 dbcheck/ 的 CSV 导入
4. 从 output/ 的 CSV 导入
"""

import sys
import csv
import sqlite3
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db_connect import get_connection

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'output'
DBCHECK_DIR = PROJECT_ROOT / 'dbcheck'

DBCHECK_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def export_to_dbcheck():
    """备份数据库到 dbcheck/"""
    print("📤 数据库备份到 dbcheck/")
    
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 导出综合类
    cursor.execute("SELECT normalized_score, title, url, crawl_time FROM hot_rank_common ORDER BY crawl_time DESC")
    rows = cursor.fetchall()
    if rows:
        common_file = DBCHECK_DIR / f"综合类_备份_{timestamp}.csv"
        with open(common_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['归一化序号', '新闻标题', 'URL', '爬取时间'])
            for row in rows:
                writer.writerow([row[0], row[1], row[2], row[3][:16] if row[3] else ''])
        print(f"✅ 综合类备份 {len(rows)} 条 → {common_file.name}")
    
    # 导出科技类
    cursor.execute("SELECT normalized_score, title, url, crawl_time FROM hot_rank_tech ORDER BY crawl_time DESC")
    rows = cursor.fetchall()
    if rows:
        tech_file = DBCHECK_DIR / f"科技类_备份_{timestamp}.csv"
        with open(tech_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['归一化序号', '新闻标题', 'URL', '爬取时间'])
            for row in rows:
                writer.writerow([row[0], row[1], row[2], row[3][:16] if row[3] else ''])
        print(f"✅ 科技类备份 {len(rows)} 条 → {tech_file.name}")
    
    conn.close()


def clear_database():
    """清空数据库"""
    print("🗑️  清空数据库")
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM hot_rank_common")
    common_count = cursor.rowcount
    cursor.execute("DELETE FROM hot_rank_tech")
    tech_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"✅ 已删除综合类 {common_count} 条，科技类 {tech_count} 条")


def import_from_dbcheck():
    """从 dbcheck/ 导入数据"""
    print("📥 从 dbcheck/ 导入数据库")
    
    common_files = sorted(DBCHECK_DIR.glob("综合类_备份_*.csv"), reverse=True)
    tech_files = sorted(DBCHECK_DIR.glob("科技类_备份_*.csv"), reverse=True)
    
    if not common_files and not tech_files:
        print("⚠️ dbcheck/ 中没有备份文件")
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if common_files:
        file_path = common_files[0]
        print(f"📂 使用综合类备份：{file_path.name}")
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                cursor.execute(
                    "INSERT INTO hot_rank_common (normalized_score, title, url, crawl_time) VALUES (?, ?, ?, ?)",
                    (float(row['归一化序号']), row['新闻标题'], row['URL'], row['爬取时间'])
                )
                count += 1
        conn.commit()
        print(f"✅ 导入 {count} 条")
    
    if tech_files:
        file_path = tech_files[0]
        print(f"📂 使用科技类备份：{file_path.name}")
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                cursor.execute(
                    "INSERT INTO hot_rank_tech (normalized_score, title, url, crawl_time) VALUES (?, ?, ?, ?)",
                    (float(row['归一化序号']), row['新闻标题'], row['URL'], row['爬取时间'])
                )
                count += 1
        conn.commit()
        print(f"✅ 导入 {count} 条")
    
    conn.close()


def import_from_output():
    """从 output/ 导入 CSV 文件"""
    print("📥 从 output/ 导入数据库")
    
    common_files = sorted(OUTPUT_DIR.glob("综合类_热榜_*.csv"), reverse=True)
    tech_files = sorted(OUTPUT_DIR.glob("科技类_热榜_*.csv"), reverse=True)
    
    if not common_files and not tech_files:
        print("⚠️ output/ 中没有 CSV 文件")
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for file_path in common_files:
        print(f"📄 处理：{file_path.name}")
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                cursor.execute(
                    "INSERT INTO hot_rank_common (normalized_score, title, url, crawl_time) VALUES (?, ?, ?, ?)",
                    (float(row['归一化序号']), row['新闻标题'], row['URL'], row['爬取时间'])
                )
                count += 1
        conn.commit()
        print(f"   → 导入 {count} 条")
    
    for file_path in tech_files:
        print(f"📄 处理：{file_path.name}")
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                cursor.execute(
                    "INSERT INTO hot_rank_tech (normalized_score, title, url, crawl_time) VALUES (?, ?, ?, ?)",
                    (float(row['归一化序号']), row['新闻标题'], row['URL'], row['爬取时间'])
                )
                count += 1
        conn.commit()
        print(f"   → 导入 {count} 条")
    
    conn.close()


def show_menu():
    """显示功能菜单"""
    print("\n" + "=" * 60)
    print("🔧 社交媒体热点词分析平台 - 数据库测试工具")
    print("=" * 60)
    print("1. 数据库备份到 dbcheck/")
    print("2. 清空数据库")
    print("3. 从 dbcheck/ 的 CSV 导入")
    print("4. 从 output/ 的 CSV 导入")
    print("0. 退出")
    print("=" * 60)


if __name__ == "__main__":
    while True:
        show_menu()
        choice = input("请选择功能 (0-4): ").strip()
        
        if choice == '1':
            export_to_dbcheck()
        elif choice == '2':
            confirm = input("⚠️  确认清空数据库？(y/n): ").strip().lower()
            if confirm == 'y':
                clear_database()
        elif choice == '3':
            import_from_dbcheck()
        elif choice == '4':
            import_from_output()
        elif choice == '0':
            print("👋 退出工具")
            break
        else:
            print("⚠️  无效选择")
        
        input("\n按回车键继续...")