#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
Flask 后端服务

功能：
1. 提供 API 接口获取热点排行数据
2. 提供 API 接口获取词云图片
3. 提供 API 接口获取情感分析数据
4. 提供 API 接口获取科技热点排行
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, send_file, request
from flask_cors import CORS

# 创建 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='../static')
CORS(app)

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
RANKINGS_DIR = os.path.join(OUTPUT_DIR, 'rankings')
WORDCLOUDS_DIR = os.path.join(OUTPUT_DIR, 'wordclouds')
SENTIMENT_DIR = os.path.join(OUTPUT_DIR, 'sentiment')


def get_latest_file(directory, prefix):
    """
    获取目录中最新的文件
    
    Args:
        directory: 目录路径
        prefix: 文件名前缀
        
    Returns:
        最新文件路径，如果没有则返回 None
    """
    if not os.path.exists(directory):
        return None
    
    files = [f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith('.json')]
    if not files:
        return None
    
    latest = max(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
    return os.path.join(directory, latest)


def get_latest_image(directory, prefix):
    """
    获取目录中最新的图片
    
    Args:
        directory: 目录路径
        prefix: 文件名前缀
        
    Returns:
        最新图片路径，如果没有则返回 None
    """
    if not os.path.exists(directory):
        return None
    
    files = [f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith('.png')]
    if not files:
        return None
    
    latest = max(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
    return os.path.join(directory, latest)


@app.route('/')
def index():
    """首页"""
    return render_template('service.html')


@app.route('/api/general_ranking')
def get_general_ranking():
    """
    获取综合热榜排行
    """
    ranking_file = get_latest_file(RANKINGS_DIR, 'ranking_general_')
    if not ranking_file:
        return jsonify({'error': '未找到综合排行数据'}), 404
    
    with open(ranking_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 返回前20条
    return jsonify({
        'success': True,
        'data': data[:20],
        'total': len(data),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/tech_ranking')
def get_tech_ranking():
    """
    获取科技热榜排行
    """
    ranking_file = get_latest_file(RANKINGS_DIR, 'ranking_tech_')
    if not ranking_file:
        return jsonify({'error': '未找到科技排行数据'}), 404
    
    with open(ranking_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return jsonify({
        'success': True,
        'data': data,
        'total': len(data),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/general_wordcloud')
def get_general_wordcloud():
    """
    获取综合热榜词云图片
    """
    image_file = get_latest_image(WORDCLOUDS_DIR, 'wordcloud_general_')
    if not image_file:
        return jsonify({'error': '未找到综合词云图片'}), 404
    
    return send_file(image_file, mimetype='image/png')


@app.route('/api/tech_wordcloud')
def get_tech_wordcloud():
    """
    获取科技热榜词云图片
    """
    image_file = get_latest_image(WORDCLOUDS_DIR, 'wordcloud_tech_')
    if not image_file:
        return jsonify({'error': '未找到科技词云图片'}), 404
    
    return send_file(image_file, mimetype='image/png')


@app.route('/api/general_sentiment')
def get_general_sentiment():
    """
    获取综合热榜情感分析数据
    """
    # 优先使用 sentiment_general_ 前缀，如果没有则尝试 sentiment_all_
    sentiment_file = get_latest_file(SENTIMENT_DIR, 'sentiment_general_')
    if not sentiment_file:
        sentiment_file = get_latest_file(SENTIMENT_DIR, 'sentiment_all_')
    
    if not sentiment_file:
        return jsonify({'error': '未找到综合情感分析数据'}), 404
    
    with open(sentiment_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 计算情感统计
    sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
    scores = []
    
    for item in data:
        label = item.get('sentiment_label', 'neutral')
        sentiment_counts[label] = sentiment_counts.get(label, 0) + 1
        scores.append(item.get('sentiment_score', 0.5))
    
    total = len(data)
    avg_score = sum(scores) / total if total > 0 else 0.5
    
    return jsonify({
        'success': True,
        'data': data,
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
    """
    获取科技热榜情感分析数据
    """
    sentiment_file = get_latest_file(SENTIMENT_DIR, 'sentiment_tech_')
    if not sentiment_file:
        return jsonify({'error': '未找到科技情感分析数据'}), 404
    
    with open(sentiment_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
    scores = []
    
    for item in data:
        label = item.get('sentiment_label', 'neutral')
        sentiment_counts[label] = sentiment_counts.get(label, 0) + 1
        scores.append(item.get('sentiment_score', 0.5))
    
    total = len(data)
    avg_score = sum(scores) / total if total > 0 else 0.5
    
    return jsonify({
        'success': True,
        'data': data,
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


@app.route('/api/hotword_detail/<int:rank>')
def get_hotword_detail(rank):
    """
    获取热点词详情（用于点击查看详情）
    
    Args:
        rank: 排名（1-based）
    """
    # 从请求参数中获取类型，默认为 general
    hot_type = request.args.get('type', 'general')
    
    if hot_type == 'tech':
        ranking_file = get_latest_file(RANKINGS_DIR, 'ranking_tech_')
    else:
        ranking_file = get_latest_file(RANKINGS_DIR, 'ranking_general_')
        if not ranking_file:
            ranking_file = get_latest_file(RANKINGS_DIR, 'ranking_all_')
    
    if not ranking_file:
        return jsonify({'error': '未找到排行数据'}), 404
    
    with open(ranking_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if rank < 1 or rank > len(data):
        return jsonify({'error': '排名超出范围'}), 404
    
    item = data[rank - 1]
    
    return jsonify({
        'success': True,
        'data': item
    })


@app.route('/api/refresh')
def refresh_data():
    """
    手动刷新数据（重新运行排名处理）
    注意：实际刷新需要调用 ranking_processor.py
    """
    # 这里可以触发重新运行 ranking_processor.py
    # 由于需要后台执行，这里只返回提示
    return jsonify({
        'success': True,
        'message': '数据刷新请求已接收，请稍后查看最新数据'
    })


if __name__ == '__main__':
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     社交媒体热点词分析平台 - Flask 后端服务                    ║
╠══════════════════════════════════════════════════════════════╣
║  服务地址: http://127.0.0.1:5000                             ║
║  综合排行: /api/general_ranking                              ║
║  科技排行: /api/tech_ranking                                 ║
║  综合词云: /api/general_wordcloud                            ║
║  科技词云: /api/tech_wordcloud                               ║
║  综合情感: /api/general_sentiment                            ║
║  科技情感: /api/tech_sentiment                               ║
║  热点详情: /api/hotword_detail/<rank>?type=general/tech      ║
╠══════════════════════════════════════════════════════════════╣
║  按 Ctrl+C 停止服务                                           ║
╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(debug=True, host='0.0.0.0', port=5000)