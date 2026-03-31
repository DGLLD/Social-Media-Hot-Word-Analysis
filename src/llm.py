#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 热点分析模块 - 独立服务 (基于 search_hotlist.py 逻辑)
功能：
1. 根据关键词搜索数据库（综合 + 科技）
2. 调用阿里云百炼 API 进行热点分析
配置：完全沿用 search_hotlist.py
"""
import sqlite3
import requests
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional

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
# 路径配置 (与 app.py 保持一致)
# ================================
# 假设 llm.py 与 app.py 同级，且 app.py 中 PROJECT_ROOT = parent.parent
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'database' / 'hotspot.db'

# ================================
# 【核心配置】阿里云百炼 API 配置 (照搬 search_hotlist.py)
# ================================
DASHSCOPE_API_KEY = "sk-7ac9c9b22a2c45a6aa93826b769cfd90"  # ⚠️ 请确保此 Key 有效
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
DASHSCOPE_MODEL = "qwen3-vl-flash"
MAX_ITEMS_FOR_AI = 10  # 发送给 AI 的最大词条数
MAX_CONTEXT_TOKENS = 12000

# ================================
# 【Prompt 模板】 (照搬 search_hotlist.py)
# ================================
AI_PROMPT_TEMPLATE = """
你是一名热点事件分析助手。请根据以下热搜词条分析关键词"{keyword}"最近发生了什么。
【热搜词条列表】
{items_text}
请分析以下内容，要求输出精炼简洁：
1. 最近发生了什么事件
2. 为什么会上热搜
3. 背景原因和详细事件经过
输出要求：
- 基于提供的词条信息分析，不要编造
- 简单分段即可，不要分点列举
- 语言精炼，控制在 500 字以内
- 如有不确定信息请明确说明
"""

# ================================
# 数据库搜索函数
# ================================
def get_connection():
    """获取数据库连接"""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"❌ 数据库文件不存在：{DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def search_by_keyword(keyword: str) -> Tuple[List[Dict], List[Dict]]:
    """
    按关键词搜索热榜数据
    Returns: (综合类结果，科技类结果)
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        search_pattern = f"%{keyword}%"
        
        # 查询综合类
        cursor.execute("""
            SELECT title, url, crawl_time FROM hot_rank_common 
            WHERE title LIKE ? ORDER BY crawl_time DESC
        """, (search_pattern,))
        common_results = [dict(row) for row in cursor.fetchall()]
        
        # 查询科技类
        cursor.execute("""
            SELECT title, url, crawl_time FROM hot_rank_tech 
            WHERE title LIKE ? ORDER BY crawl_time DESC
        """, (search_pattern,))
        tech_results = [dict(row) for row in cursor.fetchall()]
        
        # 日志：分板块输出
        logger.info(f"🔍 搜索关键词：{keyword}")
        logger.info(f"📊 [综合类] 匹配 {len(common_results)} 条")
        logger.info(f"📊 [科技类] 匹配 {len(tech_results)} 条")
        
        return common_results, tech_results
    except Exception as e:
        logger.error(f"❌ 搜索失败：{e}")
        return [], []
    finally:
        if conn: conn.close()

def merge_results(common: List[Dict], tech: List[Dict]) -> List[Dict]:
    """合并结果并去重（用于前端展示）"""
    seen = set()
    merged = []
    for item in common + tech:
        if item['title'] not in seen:
            seen.add(item['title'])
            merged.append(item)
    return merged

def build_items_text(results: List[Dict], max_items: int = 10) -> str:
    """构建 AI 分析的词条文本"""
    items_text = ""
    for idx, item in enumerate(results[:max_items], 1):
        items_text += f"{idx}. {item['title']}\n"
        items_text += f"   出处：{item['url']}\n"
    return items_text

def call_dashscope_api(keyword: str, items_text: str) -> Optional[str]:
    """调用阿里云百炼 API"""
    if not DASHSCOPE_API_KEY:
        logger.error("⚠️ API Key 未配置")
        return None
    
    prompt = AI_PROMPT_TEMPLATE.format(keyword=keyword, items_text=items_text)
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": DASHSCOPE_MODEL,
        "messages": [
            {"role": "system", "content": "你是一名专业的热点事件分析助手。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
        "stream": False
    }
    
    logger.info("🤖 正在调用 AI 模型...")
    start_time = time.time()
    try:
        response = requests.post(DASHSCOPE_API_URL, headers=headers, json=payload, timeout=60)
        elapsed = time.time() - start_time
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.info(f"✅ AI 响应完成！耗时：{elapsed:.2f} 秒")
            return content
        else:
            logger.error(f"❌ API 调用失败：HTTP {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"❌ API 调用出错：{e}")
        return None

def analyze_keyword(keyword: str) -> Dict:
    """
    完整分析流程：搜索 -> 构建文本 -> 调用 AI
    Returns: { 'success': bool, 'titles': [...], 'ai_result': '...' }
    """
    # 1. 搜索
    common, tech = search_by_keyword(keyword)
    merged = merge_results(common, tech)
    
    if not merged:
        return {'success': False, 'message': '未找到相关热点词条', 'titles': [], 'ai_result': ''}
    
    # 2. 构建 AI 文本
    items_text = build_items_text(merged, MAX_ITEMS_FOR_AI)
    
    # 3. 调用 AI
    ai_result = call_dashscope_api(keyword, items_text)
    
    return {
        'success': True,
        'titles': merged,  # 前端展示用
        'ai_result': ai_result if ai_result else 'AI 分析失败，请稍后重试'
    }