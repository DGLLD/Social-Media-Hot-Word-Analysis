#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
SnowNLP情感分析模块

功能：
1. 对每条热点标题进行情感分析
2. 计算情感分数（0-1，越接近1越正面）
3. 输出情感标签（正面/中性/负面）
4. 统计整体情绪分布
5. 按分类统计情绪分布
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

try:
    from snownlp import SnowNLP
    HAS_SNOWNLP = True
except ImportError:
    HAS_SNOWNLP = False
    print("[警告] 请安装 snownlp: pip install snownlp")


class SentimentAnalyzer:
    """
    SnowNLP情感分析器
    
    情感分数范围：0-1
    - 0-0.4: 负面
    - 0.4-0.6: 中性
    - 0.6-1: 正面
    """
    
    PROJECT_NAME = "社交媒体热点词分析项目"
    
    # 情感阈值
    SENTIMENT_THRESHOLDS = {
        'negative': (0, 0.4),
        'neutral': (0.4, 0.6),
        'positive': (0.6, 1.0)
    }
    
    def __init__(self):
        """初始化情感分析器"""
        if not HAS_SNOWNLP:
            raise ImportError("请先安装 snownlp: pip install snownlp")
        
        print(f"[初始化] {self.PROJECT_NAME} - SnowNLP情感分析模块")
        print(f"[初始化] 情感阈值: 负面(0-0.4) | 中性(0.4-0.6) | 正面(0.6-1)")
    
    def get_sentiment_label(self, score: float) -> str:
        """
        根据情感分数获取情感标签
        
        Args:
            score: 情感分数（0-1）
            
        Returns:
            情感标签: 'positive', 'neutral', 'negative'
        """
        if score < 0.4:
            return 'negative'
        elif score < 0.6:
            return 'neutral'
        else:
            return 'positive'
    
    def analyze_single(self, text: str) -> Dict[str, Any]:
        """
        分析单条文本的情感
        
        Args:
            text: 文本内容
            
        Returns:
            情感分析结果字典
        """
        s = SnowNLP(text)
        sentiment_score = s.sentiments  # 0-1，越接近1越正面
        
        sentiment_label = self.get_sentiment_label(sentiment_score)
        
        # 获取关键词（用于参考）
        keywords = s.keywords(limit=3)
        
        return {
            'text': text,
            'sentiment_score': round(sentiment_score, 4),
            'sentiment_label': sentiment_label,
            'keywords': keywords,
            'length': len(text)
        }
    
    def analyze_batch(self, items: List[Dict]) -> List[Dict]:
        """
        批量分析情感
        
        Args:
            items: 数据列表，每条需包含 'title' 字段
            
        Returns:
            添加了情感分析结果的数据列表
        """
        print(f"[处理] 开始情感分析，共 {len(items)} 条数据")
        
        results = []
        for item in items:
            title = item.get('title', '')
            if not title:
                continue
            
            # 分析情感
            analysis = self.analyze_single(title)
            
            # 添加分析结果到原数据
            enhanced_item = item.copy()
            enhanced_item['sentiment_score'] = analysis['sentiment_score']
            enhanced_item['sentiment_label'] = analysis['sentiment_label']
            enhanced_item['sentiment_keywords'] = analysis['keywords']
            
            results.append(enhanced_item)
        
        print(f"[处理] 完成情感分析，共 {len(results)} 条")
        
        return results
    
    def get_sentiment_statistics(self, items: List[Dict]) -> Dict[str, Any]:
        """
        获取情感统计信息
        
        Args:
            items: 包含情感分析结果的数据列表
            
        Returns:
            情感统计字典
        """
        if not items:
            return {}
        
        # 统计情感分布
        sentiment_counts = Counter()
        sentiment_scores = []
        
        for item in items:
            label = item.get('sentiment_label', 'neutral')
            score = item.get('sentiment_score', 0.5)
            sentiment_counts[label] += 1
            sentiment_scores.append(score)
        
        total = len(items)
        
        # 计算平均情感分数
        avg_score = sum(sentiment_scores) / total if total > 0 else 0.5
        
        return {
            'total': total,
            'sentiment_distribution': {
                'positive': sentiment_counts.get('positive', 0),
                'neutral': sentiment_counts.get('neutral', 0),
                'negative': sentiment_counts.get('negative', 0)
            },
            'positive_ratio': sentiment_counts.get('positive', 0) / total if total > 0 else 0,
            'neutral_ratio': sentiment_counts.get('neutral', 0) / total if total > 0 else 0,
            'negative_ratio': sentiment_counts.get('negative', 0) / total if total > 0 else 0,
            'average_sentiment_score': round(avg_score, 4),
            'sentiment_scores': sentiment_scores
        }
    
    def print_sentiment_report(self, items: List[Dict], title: str = "情感分析报告"):
        """
        打印情感分析报告
        
        Args:
            items: 包含情感分析结果的数据列表
            title: 报告标题
        """
        stats = self.get_sentiment_statistics(items)
        
        print(f"\n{'='*70}")
        print(f" {title}")
        print(f"{'='*70}")
        
        print(f"\n【情感分布统计】")
        print(f"  总数据量: {stats['total']} 条")
        print(f"  正面情感: {stats['sentiment_distribution']['positive']} 条 ({stats['positive_ratio']*100:.1f}%)")
        print(f"  中性情感: {stats['sentiment_distribution']['neutral']} 条 ({stats['neutral_ratio']*100:.1f}%)")
        print(f"  负面情感: {stats['sentiment_distribution']['negative']} 条 ({stats['negative_ratio']*100:.1f}%)")
        print(f"  平均情感分数: {stats['average_sentiment_score']:.4f} (0-1, 越高越正面)")
        
        # 可视化情感分布
        print(f"\n【情感分布可视化】")
        print("-" * 70)
        
        pos_bar_len = int(stats['positive_ratio'] * 40)
        neu_bar_len = int(stats['neutral_ratio'] * 40)
        neg_bar_len = int(stats['negative_ratio'] * 40)
        
        print(f"  😊 正面: {'█' * pos_bar_len} {stats['positive_ratio']*100:.1f}%")
        print(f"  😐 中性: {'█' * neu_bar_len} {stats['neutral_ratio']*100:.1f}%")
        print(f"  😞 负面: {'█' * neg_bar_len} {stats['negative_ratio']*100:.1f}%")
        
        # 显示正面和负面的示例
        positive_items = [item for item in items if item.get('sentiment_label') == 'positive']
        negative_items = [item for item in items if item.get('sentiment_label') == 'negative']
        
        if positive_items:
            print(f"\n【正面示例 TOP 5】（情感分数越高越正面）")
            print("-" * 70)
            top_positive = sorted(positive_items, key=lambda x: x.get('sentiment_score', 0), reverse=True)[:5]
            for i, item in enumerate(top_positive, 1):
                title = item['title'][:50] + '...' if len(item['title']) > 50 else item['title']
                print(f"  {i}. [{item['sentiment_score']:.3f}] {title}")
        
        if negative_items:
            print(f"\n【负面示例 TOP 5】（情感分数越低越负面）")
            print("-" * 70)
            top_negative = sorted(negative_items, key=lambda x: x.get('sentiment_score', 1))[:5]
            for i, item in enumerate(top_negative, 1):
                title = item['title'][:50] + '...' if len(item['title']) > 50 else item['title']
                print(f"  {i}. [{item['sentiment_score']:.3f}] {title}")
        
        print(f"\n{'='*70}")
    
    def analyze_from_ranking_data(self, ranking_file: str, output_dir: str = None) -> Dict[str, Any]:
        """
        从排名结果文件加载数据并进行情感分析
        
        Args:
            ranking_file: 排名结果JSON文件路径
            output_dir: 输出目录
            
        Returns:
            情感分析结果
        """
        print(f"\n{'='*70}")
        print(f" 加载排名数据进行情感分析")
        print(f"{'='*70}")
        
        # 加载数据
        with open(ranking_file, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        print(f"[加载] 读取 {len(items)} 条数据: {os.path.basename(ranking_file)}")
        
        # 情感分析
        analyzed_items = self.analyze_batch(items)
        
        # 打印报告
        name = os.path.basename(ranking_file).replace('ranking_', '').replace('.json', '')
        self.print_sentiment_report(analyzed_items, f"情感分析报告 - {name}")
        
        # 保存结果
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f'sentiment_{name}_{timestamp}.json')
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analyzed_items, f, ensure_ascii=False, indent=2)
            print(f"\n[保存] 情感分析结果已保存至: {output_path}")
        
        return {
            'items': analyzed_items,
            'statistics': self.get_sentiment_statistics(analyzed_items)
        }


# ==================== 主程序入口 ====================
if __name__ == '__main__':
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # 文件路径
    rankings_dir = os.path.join(project_root, 'output', 'rankings')
    output_dir = os.path.join(project_root, 'output', 'sentiment')
    
    # 查找排名结果文件
    ranking_files = []
    if os.path.exists(rankings_dir):
        for filename in os.listdir(rankings_dir):
            if filename.startswith('ranking_') and filename.endswith('.json'):
                ranking_files.append(os.path.join(rankings_dir, filename))
    
    if not ranking_files:
        print("[错误] 未找到排名结果文件，请先运行 ranking_processor.py")
        exit(1)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化情感分析器
    analyzer = SentimentAnalyzer()
    
    # 对每个排名文件进行情感分析
    for ranking_file in ranking_files:
        print(f"\n{'─'*70}")
        print(f"处理文件: {os.path.basename(ranking_file)}")
        print(f"{'─'*70}")
        
        result = analyzer.analyze_from_ranking_data(ranking_file, output_dir)
        
        # 打印简要统计
        stats = result['statistics']
        print(f"\n  正面: {stats['sentiment_distribution']['positive']}条 | "
              f"中性: {stats['sentiment_distribution']['neutral']}条 | "
              f"负面: {stats['sentiment_distribution']['negative']}条")
        print(f"  平均情感分: {stats['average_sentiment_score']:.3f}")
    
    print(f"\n{'='*70}")
    print("[完成] 情感分析完成")
    print(f"{'='*70}")