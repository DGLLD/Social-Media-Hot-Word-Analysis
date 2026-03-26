#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
Flask 后端服务（修复版）
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, send_file, request
from flask_cors import CORS

app = Flask(__name__, 
            template_folder='templates',
            static_folder='../static')
CORS(app)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
RANKINGS_DIR = os.path.join(OUTPUT_DIR, 'rankings')
WORDCLOUDS_DIR = os.path.join(OUTPUT_DIR, 'wordclouds')
SENTIMENT_DIR = os.path.join(OUTPUT_DIR, 'sentiment')

GENERAL_TOP_N = 30
TECH_TOP_N = 10


def get_latest_file(directory, prefix):
    """获取目录中最新的文件"""
    if not os.path.exists(directory):
        return None
    files = [f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith('.json')]
    if not files:
        return None
    latest = max(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
    return os.path.join(directory, latest)


def get_latest_image(directory, prefix):
    """获取目录中最新的图片"""
    if not os.path.exists(directory):
        return None
    files = [f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith('.png')]
    if not files:
        return None
    latest = max(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
    return os.path.join(directory, latest)


@app.route('/')
def index():
    return render_template('service.html')


@app.route('/api/general_ranking')
def get_general_ranking():
    ranking_file = get_latest_file(RANKINGS_DIR, 'ranking_general_')
    if not ranking_file:
        return jsonify({'error': '未找到综合排行数据'}), 404
    
    with open(ranking_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 获取情感分析数据来补充情感标签
    sentiment_file = get_latest_file(SENTIMENT_DIR, 'sentiment_general_')
    if not sentiment_file:
        sentiment_file = get_latest_file(SENTIMENT_DIR, 'sentiment_all_')
    
    sentiment_data = {}
    if sentiment_file:
        with open(sentiment_file, 'r', encoding='utf-8') as f:
            s_data = json.load(f)
            for s_item in s_data:
                sentiment_data[s_item.get('title', '')] = s_item
    
    # 为每条数据补充情感信息
    for item in data:
        title = item.get('title', '')
        if title in sentiment_data:
            item['sentiment_score'] = sentiment_data[title].get('sentiment_score', 0.5)
            item['sentiment_label'] = sentiment_data[title].get('sentiment_label', 'neutral')
            item['sentiment_keywords'] = sentiment_data[title].get('sentiment_keywords', [])
            item['positive_words'] = sentiment_data[title].get('positive_words', [])
            item['negative_words'] = sentiment_data[title].get('negative_words', [])
        else:
            item['sentiment_score'] = 0.5
            item['sentiment_label'] = 'neutral'
            item['sentiment_keywords'] = []
            item['positive_words'] = []
            item['negative_words'] = []
    
    top_data = data[:GENERAL_TOP_N]
    return jsonify({
        'success': True,
        'data': top_data,
        'total': len(data),
        'display_count': len(top_data),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/tech_ranking')
def get_tech_ranking():
    ranking_file = get_latest_file(RANKINGS_DIR, 'ranking_tech_')
    if not ranking_file:
        return jsonify({'error': '未找到科技排行数据'}), 404
    
    with open(ranking_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 获取情感分析数据来补充情感标签
    sentiment_file = get_latest_file(SENTIMENT_DIR, 'sentiment_tech_')
    sentiment_data = {}
    if sentiment_file:
        with open(sentiment_file, 'r', encoding='utf-8') as f:
            s_data = json.load(f)
            for s_item in s_data:
                sentiment_data[s_item.get('title', '')] = s_item
    
    # 为每条数据补充情感信息
    for item in data:
        title = item.get('title', '')
        if title in sentiment_data:
            item['sentiment_score'] = sentiment_data[title].get('sentiment_score', 0.5)
            item['sentiment_label'] = sentiment_data[title].get('sentiment_label', 'neutral')
            item['sentiment_keywords'] = sentiment_data[title].get('sentiment_keywords', [])
            item['positive_words'] = sentiment_data[title].get('positive_words', [])
            item['negative_words'] = sentiment_data[title].get('negative_words', [])
        else:
            item['sentiment_score'] = 0.5
            item['sentiment_label'] = 'neutral'
            item['sentiment_keywords'] = []
            item['positive_words'] = []
            item['negative_words'] = []
    
    top_data = data[:TECH_TOP_N]
    return jsonify({
        'success': True,
        'data': top_data,
        'total': len(data),
        'display_count': len(top_data),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/general_wordcloud')
def get_general_wordcloud():
    image_file = get_latest_image(WORDCLOUDS_DIR, 'wordcloud_general_')
    if not image_file:
        return jsonify({'error': '未找到综合词云图片'}), 404
    return send_file(image_file, mimetype='image/png')


@app.route('/api/tech_wordcloud')
def get_tech_wordcloud():
    image_file = get_latest_image(WORDCLOUDS_DIR, 'wordcloud_tech_')
    if not image_file:
        return jsonify({'error': '未找到科技词云图片'}), 404
    return send_file(image_file, mimetype='image/png')


@app.route('/api/general_sentiment')
def get_general_sentiment():
    sentiment_file = get_latest_file(SENTIMENT_DIR, 'sentiment_general_')
    if not sentiment_file:
        sentiment_file = get_latest_file(SENTIMENT_DIR, 'sentiment_all_')
    
    if not sentiment_file:
        return jsonify({'error': '未找到综合情感分析数据'}), 404
    
    with open(sentiment_file, 'r', encoding='utf-8') as f:
        all_data = json.load(f)
    
    # 只取前 GENERAL_TOP_N 条用于统计
    data = all_data[:GENERAL_TOP_N]
    
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
    sentiment_file = get_latest_file(SENTIMENT_DIR, 'sentiment_tech_')
    if not sentiment_file:
        return jsonify({'error': '未找到科技情感分析数据'}), 404
    
    with open(sentiment_file, 'r', encoding='utf-8') as f:
        all_data = json.load(f)
    
    data = all_data[:TECH_TOP_N]
    
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
    hot_type = request.args.get('type', 'general')
    
    if hot_type == 'tech':
        ranking_file = get_latest_file(RANKINGS_DIR, 'ranking_tech_')
        sentiment_file = get_latest_file(SENTIMENT_DIR, 'sentiment_tech_')
    else:
        ranking_file = get_latest_file(RANKINGS_DIR, 'ranking_general_')
        if not ranking_file:
            ranking_file = get_latest_file(RANKINGS_DIR, 'ranking_all_')
        sentiment_file = get_latest_file(SENTIMENT_DIR, 'sentiment_general_')
        if not sentiment_file:
            sentiment_file = get_latest_file(SENTIMENT_DIR, 'sentiment_all_')
    
    if not ranking_file:
        return jsonify({'error': '未找到排行数据'}), 404
    
    with open(ranking_file, 'r', encoding='utf-8') as f:
        ranking_data = json.load(f)
    
    max_rank = GENERAL_TOP_N if hot_type == 'general' else TECH_TOP_N
    if rank < 1 or rank > len(ranking_data[:max_rank]):
        return jsonify({'error': f'排名超出范围，当前共{len(ranking_data[:max_rank])}条'}), 404
    
    item = ranking_data[rank - 1].copy()
    
    # 从情感分析文件补充情感数据
    if sentiment_file:
        with open(sentiment_file, 'r', encoding='utf-8') as f:
            sentiment_data = json.load(f)
        for s_item in sentiment_data:
            if s_item.get('title') == item.get('title'):
                item['sentiment_score'] = s_item.get('sentiment_score', 0.5)
                item['sentiment_label'] = s_item.get('sentiment_label', 'neutral')
                item['sentiment_keywords'] = s_item.get('sentiment_keywords', [])
                item['positive_words'] = s_item.get('positive_words', [])
                item['negative_words'] = s_item.get('negative_words', [])
                item['snow_score'] = s_item.get('snow_score', 0.5)
                break
    
    if 'sentiment_score' not in item:
        item['sentiment_score'] = 0.5
        item['sentiment_label'] = 'neutral'
        item['sentiment_keywords'] = []
        item['positive_words'] = []
        item['negative_words'] = []
    
    return jsonify({'success': True, 'data': item})


if __name__ == '__main__':
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     社交媒体热点词分析平台 - Flask 后端服务                    ║
╠══════════════════════════════════════════════════════════════╣
║  服务地址: http://127.0.0.1:5000                             ║
║  综合排行: /api/general_ranking (前{GENERAL_TOP_N}条)        ║
║  科技排行: /api/tech_ranking (前{TECH_TOP_N}条)              ║
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