#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目 - 爬虫主程序

功能：
1. 从 tophub.today 爬取热榜数据
2. 支持 10 个平台（微博、知乎、微信、百度、贴吧、36氪、少数派、虎嗅、IT之家、掘金）
3. 数据入库 SQLite
4. CSV 备份到 output/ 目录

运行方式：
    python src/crawler.py              # 正常模式（有数据则跳过）
    python src/crawler.py --force      # 强制模式（覆盖当前半天数据）

作者: 毕业实习项目组
创建时间: 2026-03-27
"""

import requests
from lxml import html
import logging
import os
import sys
import csv
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
# 导入数据库模块
# ================================
try:
    from src.db_connect import (
        save_hot_rank_common,
        save_hot_rank_tech,
        has_data_in_period,
        delete_period_data,
        get_db_stats,
        init_database,
        get_current_period
    )
except ImportError:
    from db_connect import (
        save_hot_rank_common,
        save_hot_rank_tech,
        has_data_in_period,
        delete_period_data,
        get_db_stats,
        init_database,
        get_current_period
    )

# ================================
# 路径配置
# ================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ================================
# 平台配置
# ================================
PLATFORM_CONFIG = {
    # ========== 综合类 (5个) ==========
    '微博': {'node_id': 'node-1', 'category': 'common'},
    '知乎': {'node_id': 'node-6', 'category': 'common'},
    '微信': {'node_id': 'node-5', 'category': 'common'},
    '百度': {'node_id': 'node-2', 'category': 'common'},
    '贴吧': {'node_id': 'node-3', 'category': 'common'},
    # ========== 科技类 (5个) ==========
    '36氪': {'node_id': 'node-11', 'category': 'tech'},
    '少数派': {'node_id': 'node-137', 'category': 'tech'},
    '虎嗅': {'node_id': 'node-32', 'category': 'tech'},
    'IT之家': {'node_id': 'node-119', 'category': 'tech'},
    '掘金': {'node_id': 'node-100', 'category': 'tech'}
}


# ================================
# 网络请求函数
# ================================
def fetch_homepage(url: str) -> str:
    """
    获取今日热榜首页 HTML 内容

    Args:
        url: 目标网址

    Returns:
        str: HTML 内容，失败返回 None
    """
    logger.info(f"🔍 正在访问：{url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
        'Referer': 'https://tophub.today/',
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = response.apparent_encoding
        if response.status_code == 200:
            logger.info("✅ 首页获取成功")
            return response.text
        else:
            logger.error(f"❌ HTTP 错误：{response.status_code}")
            return None
    except Exception as e:
        logger.error(f"❌ 网络请求失败：{e}")
        return None


# ================================
# 解析函数
# ================================
def parse_platform_items(tree, node_id: str, platform_name: str) -> List[Dict[str, Any]]:
    """
    使用 XPath 解析指定平台的热榜项

    Args:
        tree: lxml HTML 树
        node_id: 平台的 node-id
        platform_name: 平台名称（用于日志）

    Returns:
        list: 数据列表，每条包含 normalized_score, title, url
    """
    results = []
    logger.info(f"🔍 正在解析 [{platform_name}]...")

    container_xpath = f'//div[@id="{node_id}"]'
    all_items = tree.xpath(f'{container_xpath}//div[contains(@class,"cc-cd-cb-ll")]')
    total_count = len(all_items)
    logger.info(f"📊 找到 {total_count} 条数据")

    if not all_items:
        logger.warning(f"⚠️ 未找到数据")
        return results

    for idx, item in enumerate(all_items):
        try:
            # 提取标题
            title_elem = item.xpath('.//span[@class="t"]/text()')
            title = title_elem[0].strip() if title_elem else ""

            # 提取链接
            link_elems = item.xpath('./ancestor::a/@href[1]')
            link = link_elems[0] if link_elems else ""

            # 补全链接
            if link and not link.startswith('http'):
                link = 'https://tophub.today/' + link.lstrip('/')

            # 过滤无效数据
            if not title or len(title) < 2:
                continue

            # 计算归一化序号（越小越热）
            normalized_score = round((idx + 1) / total_count, 4)

            results.append({
                'normalized_score': normalized_score,
                'title': title,
                'url': link
            })
        except Exception as e:
            logger.error(f"❌ 解析第{idx+1}条数据失败：{e}")
            continue

    if results:
        logger.info(f"✅ [{platform_name}] 解析完成：{len(results)} 条")
    return results


def parse_all_platforms(html_content: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    解析所有平台的热榜数据

    Args:
        html_content: 首页 HTML 内容

    Returns:
        dict: 按平台名称分组的数据
    """
    logger.info("=" * 60)
    logger.info("开始解析 HTML 内容...")

    try:
        tree = html.fromstring(html_content.encode('utf-8'))
        logger.info("✅ HTML 解析成功")
    except Exception as e:
        logger.error(f"❌ HTML 解析失败：{e}")
        return {}

    all_results = {}
    for key, config in PLATFORM_CONFIG.items():
        items = parse_platform_items(tree, config['node_id'], key)
        all_results[key] = items

    return all_results


# ================================
# CSV 备份函数
# ================================
def generate_csv_backup(data_by_category: Dict[str, List[Dict]], is_auto: bool = False):
    """
    生成分类明确的 CSV 备份

    Args:
        data_by_category: {'common': [...], 'tech': [...]}
        is_auto: 是否为自动任务（影响文件名前缀）
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    prefix = 'auto_' if is_auto else ''

    # 处理综合类数据
    common_data = data_by_category.get('common', [])
    if common_data:
        common_file = OUTPUT_DIR / f"综合类_热榜_{prefix}{timestamp}.csv"
        with open(common_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['归一化序号', '新闻标题', 'URL', '爬取时间'])
            for item in common_data:
                clean_title = item['title'].replace('\n', ' ').replace('\r', ' ').strip()
                writer.writerow([
                    item['normalized_score'],
                    clean_title,
                    item['url'],
                    current_time
                ])
        logger.info(f"✅ [综合类] CSV 备份：{common_file.name}")

    # 处理科技类数据
    tech_data = data_by_category.get('tech', [])
    if tech_data:
        tech_file = OUTPUT_DIR / f"科技类_热榜_{prefix}{timestamp}.csv"
        with open(tech_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['归一化序号', '新闻标题', 'URL', '爬取时间'])
            for item in tech_data:
                clean_title = item['title'].replace('\n', ' ').replace('\r', ' ').strip()
                writer.writerow([
                    item['normalized_score'],
                    clean_title,
                    item['url'],
                    current_time
                ])
        logger.info(f"✅ [科技类] CSV 备份：{tech_file.name}")


# ================================
# 数据库保存函数
# ================================
def save_to_database(all_results: Dict[str, List[Dict]], force: bool = False) -> Tuple[int, int, int, Dict]:
    """
    将所有平台数据保存到对应数据库表

    Args:
        all_results: 按平台分组的数据
        force: 是否强制覆盖当前半天数据

    Returns:
        tuple: (总条数, 综合类入库数, 科技类入库数, 分类数据)
    """
    common_success = 0
    tech_success = 0
    total_count = 0
    data_by_category = {'common': [], 'tech': []}

    logger.info("=" * 60)
    logger.info("开始检查入库条件...")

    # 获取当前时段
    current_period = get_current_period()
    period_name = "上午" if current_period == 'morning' else "下午"
    logger.info(f"📅 当前时段：{period_name} ({datetime.now().strftime('%Y-%m-%d %H:%M')})")

    # 检查当前半天是否已有数据
    has_common_data, common_last_time = has_data_in_period('common', current_period)
    has_tech_data, tech_last_time = has_data_in_period('tech', current_period)

    # 收集所有数据
    for platform_key, data_list in all_results.items():
        if not data_list:
            logger.warning(f"⚠️ {platform_key} 无数据可保存")
            continue
        category = PLATFORM_CONFIG[platform_key].get('category', 'common')
        for item in data_list:
            total_count += 1
            data_by_category[category].append(item)

    # 汇报数据库当前情况
    stats = get_db_stats()
    logger.info("=" * 60)
    logger.info("📊 当前数据库状态：")
    logger.info(f"   综合类：{stats['common']['count']} 条，最后入库：{stats['common']['last_time']}")
    logger.info(f"   科技类：{stats['tech']['count']} 条，最后入库：{stats['tech']['last_time']}")
    logger.info("=" * 60)

    # 判断是否入库
    if force:
        logger.info("⚠️ [强制模式] 将覆盖当前半天数据...")
        delete_period_data('common', current_period)
        delete_period_data('tech', current_period)
        should_save_common = True
        should_save_tech = True
    else:
        should_save_common = not has_common_data
        should_save_tech = not has_tech_data

        if has_common_data:
            logger.warning(f"⚠️ [综合类] {period_name}已有数据 ({common_last_time})，跳过入库（仅备份 CSV）")
        if has_tech_data:
            logger.warning(f"⚠️ [科技类] {period_name}已有数据 ({tech_last_time})，跳过入库（仅备份 CSV）")

    # 综合类入库
    if should_save_common:
        logger.info("✅ [综合类] 执行入库...")
        for item in data_by_category['common']:
            crawl_time = datetime.now().strftime('%Y-%m-%d %H:00:00')
            if save_hot_rank_common(
                item['normalized_score'],
                item['title'],
                item['url'],
                crawl_time
            ):
                common_success += 1
    else:
        logger.info("⏭️ [综合类] 跳过入库")

    # 科技类入库
    if should_save_tech:
        logger.info("✅ [科技类] 执行入库...")
        for item in data_by_category['tech']:
            crawl_time = datetime.now().strftime('%Y-%m-%d %H:00:00')
            if save_hot_rank_tech(
                item['normalized_score'],
                item['title'],
                item['url'],
                crawl_time
            ):
                tech_success += 1
    else:
        logger.info("⏭️ [科技类] 跳过入库")

    logger.info("=" * 60)
    logger.info(f"💾 处理完成！总计爬取：{total_count} 条")
    logger.info(f"   - 综合类：入库 {common_success} 条 / 共 {len(data_by_category['common'])} 条")
    logger.info(f"   - 科技类：入库 {tech_success} 条 / 共 {len(data_by_category['tech'])} 条")
    logger.info("=" * 60)

    return total_count, common_success, tech_success, data_by_category


# ================================
# 主函数
# ================================
def main(force: bool = False):
    """
    爬虫主函数

    Args:
        force: 是否强制覆盖当前半天数据
    """
    logger.info("█" * 60)
    if force:
        logger.info("🚀 今日热榜爬虫启动 (强制覆盖模式)")
    else:
        logger.info("🚀 今日热榜爬虫启动 (正常模式)")
    logger.info("█" * 60)

    try:
        # 初始化数据库
        init_database()

        # 获取首页
        homepage_url = "https://tophub.today/"
        html_content = fetch_homepage(homepage_url)
        if not html_content:
            logger.error("❌ 无法获取首页内容")
            return

        # 解析数据
        all_results = parse_all_platforms(html_content)

        # 保存数据（含入库判断逻辑）
        total_count, common_count, tech_count, data_by_category = save_to_database(
            all_results,
            force=force
        )

        # CSV 备份（每次都执行，不覆盖）
        logger.info("📄 开始生成 CSV 备份...")
        generate_csv_backup(data_by_category, is_auto=False)

        logger.info("🎉 爬虫运行完成!")

    except KeyboardInterrupt:
        logger.warning("⚠️ 用户中断程序")
    except Exception as e:
        logger.error(f"❌ 程序运行出错：{e}")
        raise


# ================================
# 程序入口
# ================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='今日热榜爬虫')
    parser.add_argument('--force', action='store_true', help='强制覆盖当前半天数据')
    args = parser.parse_args()

    main(force=args.force)