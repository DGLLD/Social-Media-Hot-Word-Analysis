#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
Flask 后端服务（支持数据库 - 完整刷新功能）
功能：
1. 提供 API 接口获取热点排行数据
2. 提供 API 接口获取词云图片
3. 提供 API 接口获取情感分析数据
4. 提供 API 接口获取热点详情
5. 支持综合热榜和科技热榜切换
6. 支持手动触发数据刷新（完整流程：爬虫→清洗→排行→情感→词云）
7. 支持任务状态查询
8. 修复：AI关键词列表现在区分板块
作者：毕业实习项目组
创建时间：2026-03-27
"""
import os
import json
import sys
import subprocess
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from flask import Flask, render_template, jsonify, send_file, request
from flask_cors import CORS

# 设置日志输出到控制台
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 导入数据库模块
try:
    from src.db_connect import get_latest_data, get_db_stats
except ImportError:
    from db_connect import get_latest_data, get_db_stats

# ================================
# 【新增】导入 AI 模块 (llm.py 需在同级目录)
# ================================
try:
    from llm import analyze_keyword, search_by_keyword, merge_results
    logging.info("✅ AI 模块 (llm) 加载成功")
except ImportError as e:
    logging.warning(f"⚠️ AI 模块 (llm) 加载失败：{e}，AI 功能将不可用")
    analyze_keyword = None

# 创建 Flask 应用
app = Flask(__name__,
            template_folder='templates',
            static_folder='../static')
CORS(app)

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'output'
RANKINGS_DIR = OUTPUT_DIR / 'rankings'
WORDCLOUDS_DIR = OUTPUT_DIR / 'wordclouds' # 词云和词频文件都在这里
SENTIMENT_DIR = OUTPUT_DIR / 'sentiment'

# 显示条数配置
GENERAL_TOP_N = 30   # 综合热榜显示前 30 条
TECH_TOP_N = 10       # 科技热榜显示前 10 条

# 任务状态
refresh_status = {
    'running': False,
    'step': '',
    'start_time': None,
    'end_time': None,
    'error': None
}


# ================================
# 辅助函数
# ================================
def get_latest_file(directory: Path, prefix: str) -> Optional[Path]:
    """获取目录中最新的文件"""
    if not directory.exists():
        return None
    files = [f for f in directory.iterdir() if f.name.startswith(prefix) and f.suffix == '.json']
    if not files:
        return None
    latest = max(files, key=lambda f: f.stat().st_mtime)
    return latest


def get_latest_image(directory: Path, prefix: str) -> Optional[Path]:
    """获取目录中最新的图片"""
    if not directory.exists():
        return None
    files = [f for f in directory.iterdir() if f.name.startswith(prefix) and f.suffix == '.png']
    if not files:
        return None
    latest = max(files, key=lambda f: f.stat().st_mtime)
    return latest


def load_sentiment_data(prefix: str) -> Dict[str, Dict]:
    """加载情感分析数据，返回标题到情感信息的映射"""
    sentiment_file = get_latest_file(SENTIMENT_DIR, prefix)
    if not sentiment_file:
        return {}

    with open(sentiment_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    sentiment_map = {}
    for item in data:
        title = item.get('title', '')
        if title:
            sentiment_map[title] = {
                'sentiment_score': item.get('sentiment_score', 0.5),
                'sentiment_label': item.get('sentiment_label', 'neutral'),
                'sentiment_icon': item.get('sentiment_icon', '😐'),
                'sentiment_keywords': item.get('sentiment_keywords', []),
                'positive_words': item.get('positive_words', []),
                'negative_words': item.get('negative_words', [])
            }
    return sentiment_map


def merge_sentiment_to_ranking(ranking_data: List[Dict], sentiment_map: Dict[str, Dict]) -> List[Dict]:
    """将情感分析结果合并到排行数据中"""
    result = []
    for item in ranking_data:
        title = item.get('title', '')
        merged_item = item.copy()
        if title in sentiment_map:
            merged_item.update(sentiment_map[title])
        else:
            merged_item['sentiment_score'] = 0.5
            merged_item['sentiment_label'] = 'neutral'
            merged_item['sentiment_icon'] = '😐'
            merged_item['sentiment_keywords'] = []
            merged_item['positive_words'] = []
            merged_item['negative_words'] = []
        result.append(merged_item)
    return result


def run_full_update():
    """执行完整数据更新流程（优化版）"""
    global refresh_status
    try:
        refresh_status['running'] = True
        refresh_status['error'] = None
        refresh_status['start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 1：爬虫
        refresh_status['step'] = '爬虫执行中...'
        subprocess.run(['python', str(PROJECT_ROOT / 'src' / 'crawler.py'), '--force'],
                       cwd=str(PROJECT_ROOT), capture_output=True, timeout=120)

        # 步骤 2：数据清洗（分别处理综合和科技）
        refresh_status['step'] = '数据清洗中...'
        # subprocess.run(['python', str(PROJECT_ROOT / 'src' / 'data_cleaner.py')],
        #                cwd=str(PROJECT_ROOT), capture_output=True, timeout=60)
        # 直接调用清洗函数
        try:
            from src.data_cleaner import DataCleaner
            cleaner = DataCleaner()
            # 清洗综合数据
            cleaner.clean_from_database('common', 30, save_to_file=True)
            # 清洗科技数据
            cleaner.clean_from_database('tech', 10, save_to_file=True)
        except Exception as e:
            logging.error(f"数据清洗失败：{e}")
            # 降级：使用子进程
            subprocess.run(['python', str(PROJECT_ROOT / 'src' / 'data_cleaner.py')],
                           cwd=str(PROJECT_ROOT), capture_output=True, timeout=60)

        # 步骤 3：排行处理
        refresh_status['step'] = '排行处理中...'
        subprocess.run(['python', str(PROJECT_ROOT / 'src' / 'ranking_processor.py')],
                       cwd=str(PROJECT_ROOT), capture_output=True, timeout=120)

        # 步骤 4：情感分析（只分析前 30 条，优化速度）
        refresh_status['step'] = '情感分析中...'
        # 直接调用分析函数，而不是运行子进程
        try:
            from src.sentiment_analyzer import SentimentAnalyzer
            analyzer = SentimentAnalyzer()
            # 只分析前 30 条综合数据和前 10 条科技数据
            analyzer.analyze_from_database('common', 30)
            analyzer.analyze_from_database('tech', 10)
        except Exception as e:
            logging.error(f"情感分析失败：{e}")
            # 降级：使用子进程
            subprocess.run(['python', str(PROJECT_ROOT / 'src' / 'sentiment_analyzer.py')],
                           cwd=str(PROJECT_ROOT), capture_output=True, timeout=60)

        # 步骤 5：词云生成 (由 ranking_processor.py 内部完成)
        refresh_status['step'] = '词云生成中...'
        # ranking_processor.py 已经包含了词云生成逻辑，无需在此重复调用

        refresh_status['step'] = '完成'
        refresh_status['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    except subprocess.TimeoutExpired as e:
        refresh_status['error'] = f'步骤超时：{refresh_status["step"]}'
    except Exception as e:
        refresh_status['error'] = str(e)
    finally:
        refresh_status['running'] = False


# ================================
# 页面路由
# ================================
@app.route('/')
def index():
    """首页"""
    return render_template('service.html')


# ================================6
# API 路由 - 排行榜（合并情感数据）
# ================================
@app.route('/api/general_ranking')
def get_general_ranking():
    """获取综合热榜排行（合并情感分析结果）"""
    # 1. 加载排行数据
    ranking_file = get_latest_file(RANKINGS_DIR, 'ranking_general_')
    if not ranking_file:
        rows = get_latest_data('common', GENERAL_TOP_N)
        if rows:
            ranking_data = []
            for row in rows:
                ranking_data.append({
                    'title': row['title'],
                    'url': row['url'],
                    'raw_weight': row['normalized_score'],
                    'timestamp': row['crawl_time']
                })
        else:
            ranking_data = []
    else:
        with open(ranking_file, 'r', encoding='utf-8') as f:
            ranking_data = json.load(f)

    # 2. 加载情感分析数据
    sentiment_map = load_sentiment_data('sentiment_common_')
    if not sentiment_map:
        sentiment_map = load_sentiment_data('sentiment_general_')
    if not sentiment_map:
        sentiment_map = load_sentiment_data('sentiment_all_')

    # 3. 合并数据
    merged_data = merge_sentiment_to_ranking(ranking_data, sentiment_map)

    return jsonify({
        'success': True,
        'data': merged_data[:GENERAL_TOP_N],
        'total': len(merged_data),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/tech_ranking')
def get_tech_ranking():
    """获取科技热榜排行（合并情感分析结果）"""
    ranking_file = get_latest_file(RANKINGS_DIR, 'ranking_tech_')
    if not ranking_file:
        rows = get_latest_data('tech', TECH_TOP_N)
        if rows:
            ranking_data = []
            for row in rows:
                ranking_data.append({
                    'title': row['title'],
                    'url': row['url'],
                    'raw_weight': row['normalized_score'],
                    'timestamp': row['crawl_time']
                })
        else:
            ranking_data = []
    else:
        with open(ranking_file, 'r', encoding='utf-8') as f:
            ranking_data = json.load(f)

    sentiment_map = load_sentiment_data('sentiment_tech_')
    merged_data = merge_sentiment_to_ranking(ranking_data, sentiment_map)

    return jsonify({
        'success': True,
        'data': merged_data[:TECH_TOP_N],
        'total': len(merged_data),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


# ================================
# API 路由 - 词云
# ================================
@app.route('/api/general_wordcloud')
def get_general_wordcloud():
    """获取综合热榜词云图片"""
    image_file = get_latest_image(WORDCLOUDS_DIR, 'wordcloud_general_')
    if not image_file:
        return jsonify({'error': '未找到综合词云图片'}), 404
    return send_file(image_file, mimetype='image/png')


@app.route('/api/tech_wordcloud')
def get_tech_wordcloud():
    """获取科技热榜词云图片"""
    image_file = get_latest_image(WORDCLOUDS_DIR, 'wordcloud_tech_')
    if not image_file:
        return jsonify({'error': '未找到科技词云图片'}), 404
    return send_file(image_file, mimetype='image/png')


# ================================
# API 路由 - 情感分析统计
# ================================
@app.route('/api/general_sentiment')
def get_general_sentiment():
    """获取综合热榜情感分析统计"""
    sentiment_map = load_sentiment_data('sentiment_common_')
    if not sentiment_map:
        sentiment_map = load_sentiment_data('sentiment_general_')
    if not sentiment_map:
        sentiment_map = load_sentiment_data('sentiment_all_')

    sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
    scores = []
    for title, info in sentiment_map.items():
        label = info.get('sentiment_label', 'neutral')
        sentiment_counts[label] += 1
        scores.append(info.get('sentiment_score', 0.5))

    total = len(sentiment_map)
    avg_score = sum(scores) / total if total > 0 else 0.5

    return jsonify({
        'success': True,
        'data': list(sentiment_map.values())[:GENERAL_TOP_N],
        'statistics': {
            'total': total,
            'positive': sentiment_counts['positive'],
            'neutral': sentiment_counts['neutral'],
            'negative': sentiment_counts['negative'],
            'positive_ratio': round(sentiment_counts['positive'] / total * 100, 1) if total > 0 else 0,
            'neutral_ratio': round(sentiment_counts['neutral'] / total * 100, 1) if total > 0 else 0,
            'negative_ratio': round(sentiment_counts['negative'] / total * 100, 1) if total > 0 else 0,
            'avg_score': round(avg_score, 3)
        }
    })


@app.route('/api/tech_sentiment')
def get_tech_sentiment():
    """获取科技热榜情感分析统计"""
    sentiment_map = load_sentiment_data('sentiment_tech_')

    sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
    scores = []
    for title, info in sentiment_map.items():
        label = info.get('sentiment_label', 'neutral')
        sentiment_counts[label] += 1
        scores.append(info.get('sentiment_score', 0.5))

    total = len(sentiment_map)
    avg_score = sum(scores) / total if total > 0 else 0.5

    return jsonify({
        'success': True,
        'data': list(sentiment_map.values())[:TECH_TOP_N],
        'statistics': {
            'total': total,
            'positive': sentiment_counts['positive'],
            'neutral': sentiment_counts['neutral'],
            'negative': sentiment_counts['negative'],
            'positive_ratio': round(sentiment_counts['positive'] / total * 100, 1) if total > 0 else 0,
            'neutral_ratio': round(sentiment_counts['neutral'] / total * 100, 1) if total > 0 else 0,
            'negative_ratio': round(sentiment_counts['negative'] / total * 100, 1) if total > 0 else 0,
            'avg_score': round(avg_score, 3)
        }
    })


# ================================
# API 路由 - 热点详情
# ================================
@app.route('/api/hotword_detail/<int:rank>')
def get_hotword_detail(rank):
    """获取热点词详情"""
    hot_type = request.args.get('type', 'general')

    if hot_type == 'tech':
        ranking_file = get_latest_file(RANKINGS_DIR, 'ranking_tech_')
        sentiment_map = load_sentiment_data('sentiment_tech_')
        top_n = TECH_TOP_N
    else:
        ranking_file = get_latest_file(RANKINGS_DIR, 'ranking_general_')
        sentiment_map = load_sentiment_data('sentiment_common_')
        if not sentiment_map:
            sentiment_map = load_sentiment_data('sentiment_general_')
        if not sentiment_map:
            sentiment_map = load_sentiment_data('sentiment_all_')
        top_n = GENERAL_TOP_N

    if not ranking_file:
        return jsonify({'error': '未找到排行数据'}), 404

    with open(ranking_file, 'r', encoding='utf-8') as f:
        ranking_data = json.load(f)

    if rank < 1 or rank > len(ranking_data[:top_n]):
        return jsonify({'error': f'排名超出范围'}), 404

    item = ranking_data[rank - 1].copy()
    title = item.get('title', '')

    if title in sentiment_map:
        item.update(sentiment_map[title])
    else:
        item['sentiment_score'] = 0.5
        item['sentiment_label'] = 'neutral'
        item['sentiment_icon'] = '😐'
        item['sentiment_keywords'] = []
        item['positive_words'] = []
        item['negative_words'] = []

    return jsonify({'success': True, 'data': item})


# ================================
# API 路由 - 数据库状态
# ================================
@app.route('/api/db_stats')
def get_db_stats_api():
    """获取数据库统计信息"""
    stats = get_db_stats()
    return jsonify({
        'success': True,
        'data': {
            'common': {
                'count': stats['common']['count'],
                'last_time': stats['common']['last_time']
            },
            'tech': {
                'count': stats['tech']['count'],
                'last_time': stats['tech']['last_time']
            }
        }
    })


# ================================
# API 路由 - 刷新数据（核心功能）
# ================================
@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """
    手动触发数据刷新
    启动后台线程执行完整更新流程
    """
    global refresh_status
    if refresh_status['running']:
        return jsonify({
            'success': False,
            'message': '已有刷新任务正在执行中，请稍后再试',
            'running': True,
            'step': refresh_status['step']
        }), 409

    # 启动后台线程
    thread = threading.Thread(target=run_full_update)
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'message': '数据刷新已启动，请稍后查看最新数据',
        'running': True,
        'step': '已启动'
    })


@app.route('/api/refresh/status', methods=['GET'])
def get_refresh_status():
    """获取刷新任务状态"""
    global refresh_status
    return jsonify({
        'success': True,
        'running': refresh_status['running'],
        'step': refresh_status['step'],
        'start_time': refresh_status['start_time'],
        'end_time': refresh_status['end_time'],
        'error': refresh_status['error']
    })


# ================================
# API 路由 - AI 热词列表（修复版：区分板块）
# ================================
@app.route('/api/llm/keywords', methods=['GET'])
def get_llm_keywords():
    """获取指定板块的词云 Top20 关键词"""
    # 获取请求参数，确定是哪个板块
    hot_type = request.args.get('type', 'general').lower() # 默认为 'general'

    # 根据板块类型确定前缀
    if hot_type == 'tech':
        prefix = 'word_freq_tech_'
        logging.info(f"🔍 [AI Keywords] 请求科技板块词频") # 日志
    elif hot_type == 'general':
        prefix = 'word_freq_general_' # 注意：这里假设 wordcloud_generator.py 生成的是这种格式
        logging.info(f"🔍 [AI Keywords] 请求综合板块词频") # 日志
    else:
        # 如果 type 参数不是 tech 或 general，则返回错误
        return jsonify({'success': False, 'message': 'Invalid type. Use "general" or "tech".'}), 400

    # 查找对应板块的最新词频文件 (在 output/wordclouds/ 目录下查找)
    freq_file = get_latest_file(WORDCLOUDS_DIR, prefix) # 使用 WORDCLOUDS_DIR
    if not freq_file:
        logging.warning(f"❌ [AI Keywords] 未找到板块 '{hot_type}' 的词频文件，前缀: {prefix}")
        return jsonify({'success': False, 'message': f'未找到{hot_type}板块的词云数据'}), 404

    try:
        with open(freq_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        keywords = [item['word'] for item in data[:20]]
        logging.info(f"✅ [AI Keywords] 成功获取板块 '{hot_type}' 的 {len(keywords)} 个关键词")
        return jsonify({'success': True, 'data': keywords, 'type': hot_type}) # 增加 type 信息方便调试
    except Exception as e:
        logging.error(f"❌ [AI Keywords] 读取词频失败：{e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/llm/search', methods=['GET'])
def llm_search():
    """步骤 1：搜索相关词条"""
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify({'success': False, 'message': '关键词不能为空'}), 400

    try:
        common, tech = search_by_keyword(keyword)
        merged = merge_results(common, tech)
        logging.info(f"🔍 [AI 搜索] 关键词：{keyword}, 结果数：{len(merged)}")
        return jsonify({'success': True, 'data': merged})
    except Exception as e:
        logging.error(f"❌ [AI 搜索] 出错：{e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/llm/analyze', methods=['POST'])
def llm_analyze():
    """步骤 2：启动 AI 分析"""
    if not analyze_keyword:
        return jsonify({'success': False, 'message': 'AI 模块未加载'}), 503

    data = request.json
    keyword = data.get('keyword', '').strip()
    if not keyword:
        return jsonify({'success': False, 'message': '关键词不能为空'}), 400

    try:
        logging.info(f"🤖 [AI 分析] 启动：{keyword}")
        result = analyze_keyword(keyword)
        return jsonify(result)
    except Exception as e:
        logging.error(f"❌ [AI 分析] 出错：{e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ================================
# 启动服务
# ================================
if __name__ == '__main__':
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     社交媒体热点词分析平台 - Flask 后端服务                    ║
╠══════════════════════════════════════════════════════════════╣
║  服务地址：http://127.0.0.1:5000                             ║
║  综合排行：/api/general_ranking (前{GENERAL_TOP_N}条)        ║
║  科技排行：/api/tech_ranking (前{TECH_TOP_N}条)              ║
║  综合词云：/api/general_wordcloud                            ║
║  科技词云：/api/tech_wordcloud                               ║
║  综合情感：/api/general_sentiment                            ║
║  科技情感：/api/tech_sentiment                               ║
║  热点详情：/api/hotword_detail/<rank>?type=general/tech      ║
║  数据库状态：/api/db_stats                                   ║
║  刷新数据：POST /api/refresh                                 ║
║  刷新状态：GET /api/refresh/status                           ║
║  【新增】AI 问答：/api/llm/keywords, /search, /analyze        ║
║  【修复】AI关键词列表区分板块：/api/llm/keywords?type=tech/general ║
╠══════════════════════════════════════════════════════════════╣
║  按 Ctrl+C 停止服务                                           ║
╚══════════════════════════════════════════════════════════════╝
""")
    app.run(debug=True, host='0.0.0.0', port=5000)
