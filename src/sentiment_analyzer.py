#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
SnowNLP情感分析模块（增强版）

功能：
1. 对每条热点标题进行情感分析
2. 使用情感词典增强判断
3. 计算情感分数（0-1，越接近1越正面）
4. 输出情感标签（正面/中性/负面）
5. 统计整体情绪分布
6. 按分类统计情绪分布
"""

import os
import json
import re
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
    SnowNLP情感分析器（增强版）
    使用情感词典 + SnowNLP 双重判断
    """
    
    PROJECT_NAME = "社交媒体热点词分析项目"
    
    # 情感阈值
    SENTIMENT_THRESHOLDS = {
        'negative': (0, 0.4),
        'neutral': (0.4, 0.6),
        'positive': (0.6, 1.0)
    }
    
    # 正面情感词典
    POSITIVE_WORDS = {
        '突破', '大涨', '利好', '新高', '夺冠', '创新', '领先', '增长',
        '成功', '优秀', '进步', '发展', '提升', '改善', '好转', '回暖',
        '爆发', '崛起', '腾飞', '辉煌', '卓越', '惊艳', '震撼', '火爆',
        '热销', '抢购', '涨停', '飙升', '暴涨', '猛涨', '大幅上涨',
        '祝贺', '恭喜', '点赞', '支持', '称赞', '好评', '认可', '肯定',
        '里程碑', '突破性', '重大进展', '历史性', '首次', '首创'
    }
    
    # 负面情感词典
    NEGATIVE_WORDS = {
        '暴跌', '崩盘', '危机', '下跌', '争议', '风险', '调查', '下滑',
        '失败', '问题', '困难', '挑战', '压力', '紧张', '冲突', '战争',
        '死亡', '去世', '逝世', '猝死', '心梗', '事故', '灾难', '警告', '警惕',
        '造假', '欺诈', '骗局', '曝光', '查封', '立案', '处罚', '罚款',
        '抓捕', '被捕', '拘留', '起诉', '诉讼', '纠纷', '矛盾', '对抗',
        '恶化', '衰退', '萎缩', '低迷', '疲软', '乏力', '亏损', '负债',
        '裁员', '降薪', '倒闭', '破产', '违约', '失信', '违规', '违法'
    }
    
    # 死亡相关关键词（强负面）
    DEATH_KEYWORDS = {
        '去世', '逝世', '猝死', '心梗', '死亡', '遇难', '牺牲',
        '离世', '病逝', '过世', '走了', '不幸'
    }
    
    # 正面事件关键词（强正面）
    POSITIVE_EVENTS = {
        '捐款', '资助', '救助', '捐赠', '援助', '帮扶', '关爱',
        '突破', '大涨', '夺冠', '创新', '里程碑', '历史性'
    }
    
    # 中性事件关键词（用于平衡）
    NEUTRAL_KEYWORDS = {
        '发布', '宣布', '召开', '举行', '举办', '开展', '启动',
        '回应', '表态', '说明', '解释', '澄清', '否认', '确认',
        '报道', '消息', '据悉', '据了解'
    }
    
    def __init__(self):
        """初始化情感分析器"""
        if not HAS_SNOWNLP:
            raise ImportError("请先安装 snownlp: pip install snownlp")
        
        print(f"[初始化] {self.PROJECT_NAME} - SnowNLP情感分析模块（增强版）")
        print(f"[初始化] 情感阈值: 负面(0-0.4) | 中性(0.4-0.6) | 正面(0.6-1)")
        print(f"[初始化] 正面词库: {len(self.POSITIVE_WORDS)}个")
        print(f"[初始化] 负面词库: {len(self.NEGATIVE_WORDS)}个")
    
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
    
    def get_sentiment_icon(self, label: str) -> str:
        """获取情感图标"""
        icons = {
            'positive': '😊',
            'neutral': '😐',
            'negative': '😞'
        }
        return icons.get(label, '😐')
    
    def enhance_with_lexicon(self, text: str, snow_score: float) -> float:
        """
        使用情感词典增强判断
        
        Args:
            text: 文本内容
            snow_score: SnowNLP原始分数
            
        Returns:
            增强后的情感分数
        """
        # 统计正面和负面词出现次数
        pos_count = 0
        neg_count = 0
        
        for word in self.POSITIVE_WORDS:
            if word in text:
                pos_count += 1
        
        for word in self.NEGATIVE_WORDS:
            if word in text:
                neg_count += 1
        
        # 计算词库倾向
        if pos_count + neg_count > 0:
            lexicon_score = pos_count / (pos_count + neg_count)
            # 加权混合：SnowNLP 60% + 词库 40%
            enhanced_score = snow_score * 0.6 + lexicon_score * 0.4
        else:
            enhanced_score = snow_score
        
        # 特殊处理：死亡相关词汇直接判定为负面
        for kw in self.DEATH_KEYWORDS:
            if kw in text:
                enhanced_score = min(enhanced_score, 0.2)
                break
        
        # 特殊处理：正面事件词汇
        for kw in self.POSITIVE_EVENTS:
            if kw in text:
                enhanced_score = max(enhanced_score, 0.65)
                break
        
        # 处理：同时包含正面和负面词
        if pos_count > 0 and neg_count > 0:
            # 如果同时出现，取平均并偏向中性
            enhanced_score = (enhanced_score + 0.5) / 2
        
        # 限制范围
        enhanced_score = max(0.0, min(1.0, enhanced_score))
        
        return round(enhanced_score, 4)
    
    def analyze_single(self, text: str) -> Dict[str, Any]:
        """
        分析单条文本的情感（增强版）
        
        Args:
            text: 文本内容
            
        Returns:
            情感分析结果字典
        """
        s = SnowNLP(text)
        snow_score = s.sentiments  # 0-1，越接近1越正面
        
        # 使用情感词典增强
        enhanced_score = self.enhance_with_lexicon(text, snow_score)
        sentiment_label = self.get_sentiment_label(enhanced_score)
        sentiment_icon = self.get_sentiment_icon(sentiment_label)
        
        # 获取关键词
        keywords = s.keywords(limit=5)
        
        # 统计情感词
        pos_words_found = [w for w in self.POSITIVE_WORDS if w in text]
        neg_words_found = [w for w in self.NEGATIVE_WORDS if w in text]
        
        return {
            'text': text,
            'snow_score': round(snow_score, 4),
            'sentiment_score': enhanced_score,
            'sentiment_label': sentiment_label,
            'sentiment_icon': sentiment_icon,
            'keywords': keywords,
            'positive_words': pos_words_found[:3],
            'negative_words': neg_words_found[:3],
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
        stats = {'positive': 0, 'neutral': 0, 'negative': 0}
        
        for item in items:
            title = item.get('title', '')
            if not title:
                continue
            
            # 分析情感
            analysis = self.analyze_single(title)
            
            # 更新统计
            stats[analysis['sentiment_label']] += 1
            
            # 添加分析结果到原数据
            enhanced_item = item.copy()
            enhanced_item['sentiment_score'] = analysis['sentiment_score']
            enhanced_item['sentiment_label'] = analysis['sentiment_label']
            enhanced_item['sentiment_icon'] = analysis['sentiment_icon']
            enhanced_item['sentiment_keywords'] = analysis['keywords']
            enhanced_item['snow_score'] = analysis['snow_score']
            enhanced_item['positive_words'] = analysis['positive_words']
            enhanced_item['negative_words'] = analysis['negative_words']
            
            results.append(enhanced_item)
        
        print(f"[处理] 完成情感分析，共 {len(results)} 条")
        print(f"[统计] 正面: {stats['positive']} | 中性: {stats['neutral']} | 负面: {stats['negative']}")
        
        # 打印分析示例
        print("\n【情感分析示例】")
        for i, item in enumerate(results[:8], 1):
            label = item['sentiment_label']
            icon = item['sentiment_icon']
            score = item['sentiment_score']
            title = item['title'][:45] + '...' if len(item['title']) > 45 else item['title']
            print(f"  {i}. {icon} [{label}:{score:.3f}] {title}")
        
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
        
        # 找出最正面和最负面的标题
        positive_items = [item for item in items if item.get('sentiment_label') == 'positive']
        negative_items = [item for item in items if item.get('sentiment_label') == 'negative']
        
        top_positive = sorted(positive_items, key=lambda x: x.get('sentiment_score', 0), reverse=True)[:3] if positive_items else []
        top_negative = sorted(negative_items, key=lambda x: x.get('sentiment_score', 1))[:3] if negative_items else []
        
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
            'sentiment_scores': sentiment_scores,
            'top_positive': [{'title': item['title'][:50], 'score': item['sentiment_score']} for item in top_positive],
            'top_negative': [{'title': item['title'][:50], 'score': item['sentiment_score']} for item in top_negative]
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
        print(f"  😊 正面情感: {stats['sentiment_distribution']['positive']} 条 ({stats['positive_ratio']*100:.1f}%)")
        print(f"  😐 中性情感: {stats['sentiment_distribution']['neutral']} 条 ({stats['neutral_ratio']*100:.1f}%)")
        print(f"  😞 负面情感: {stats['sentiment_distribution']['negative']} 条 ({stats['negative_ratio']*100:.1f}%)")
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
        
        # 显示最正面和最负面的示例
        if stats['top_positive']:
            print(f"\n【最正面示例 TOP 3】")
            for i, item in enumerate(stats['top_positive'], 1):
                print(f"  {i}. [{item['score']:.3f}] {item['title']}")
        
        if stats['top_negative']:
            print(f"\n【最负面示例 TOP 3】")
            for i, item in enumerate(stats['top_negative'], 1):
                print(f"  {i}. [{item['score']:.3f}] {item['title']}")
        
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
    
    # 查找排名结果文件（优先使用 general 和 tech）
    ranking_files = []
    if os.path.exists(rankings_dir):
        # 优先使用 general 和 tech 文件
        for prefix in ['ranking_general_', 'ranking_tech_', 'ranking_all_']:
            for filename in os.listdir(rankings_dir):
                if filename.startswith(prefix) and filename.endswith('.json'):
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