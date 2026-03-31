#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
SnowNLP情感分析模块（高精度版）
"""

import os
import json
import sys
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from snownlp import SnowNLP
    HAS_SNOWNLP = True
except ImportError:
    HAS_SNOWNLP = False
    print("[警告] 请安装 snownlp: pip install snownlp")

try:
    from src.db_connect import get_latest_data, get_db_stats
except ImportError:
    from db_connect import get_latest_data, get_db_stats

try:
    from src.data_cleaner import DataCleaner
except ImportError:
    from data_cleaner import DataCleaner


class SentimentAnalyzer:
    PROJECT_NAME = "社交媒体热点词分析项目"

    SENTIMENT_THRESHOLDS = {
        'negative': (0, 0.4),
        'neutral': (0.4, 0.6),
        'positive': (0.6, 1.0)
    }

      # ==================== 正面情感词典 ====================
    POSITIVE_WORDS = {
        '突破', '大涨', '利好', '新高', '夺冠', '创新', '领先', '增长',
        '成功', '优秀', '进步', '发展', '提升', '改善', '好转', '回暖',
        '爆发', '崛起', '腾飞', '辉煌', '卓越', '惊艳', '震撼', '火爆',
        '热销', '抢购', '涨停', '飙升', '暴涨', '猛涨', '大幅上涨',
        '里程碑', '突破性', '重大进展', '历史性', '首次', '首创',
        '开源', '开源项目', '发布', '上线', '推出', '亮相', '展示',
        '攻克', '治愈', '康复', '痊愈', '救活', '挽救', '奇迹',
        '祝贺', '恭喜', '点赞', '支持', '称赞', '好评', '认可', '肯定',
        '致敬', '缅怀', '纪念', '感动', '温暖', '振奋',
        '增长', '回升', '回暖', '复苏', '企稳', '向好', '红利',
        '幸福', '快乐', '开心', '高兴', '激动', '兴奋', '骄傲', '自豪',
        '期待', '向往', '希望', '信心', '信任',
        # 教程/推荐类
        '教程', '指南', '攻略', '亲测', '实测', '推荐', '神器', '必备',
        '工具', '技巧', '干货', '经验', '分享', '总结', '心得',
        '效率', '拉满', '翻倍', '加速', '优化', '提升',
        # 正面事件
        '夺冠', '金牌', '胜利', '凯旋', '荣誉', '表彰', '获奖',
        '签约', '合作', '战略', '协议', '投资', '融资',
    }

    # ==================== 负面情感词典（增强版）====================
    NEGATIVE_WORDS = {
        # 经济负面
        '暴跌', '崩盘', '危机', '下跌', '下滑', '亏损', '负债', '破产',
        '倒闭', '裁员', '降薪', '违约', '失信', '违规', '违法',
        '净亏损', '由盈转亏',
        # 社会负面
        '争议', '风险', '调查', '纠纷', '冲突', '对抗', '紧张',
        '战争', '袭击', '轰炸', '空袭', '导弹',
        '示威', '抗议', '游行', '暴乱', '骚乱',
        # 死亡/悲剧（增强）
        '身亡', '去世', '逝世', '猝死', '心梗', '死亡', '遇难', '牺牲',
        '离世', '病逝', '过世', '不幸', '悲剧', '惨剧', '惨案', '血案',
        '命案', '凶杀', '杀人', '杀害', '谋杀', '高发', '蔓延', '爆发',
        '遗体', '失联', '失踪', '坠毁', '沉没',
        # 关押/虐待
        '关押', '监禁', '囚禁', '炼狱', '地狱', '折磨', '虐待', '酷刑',
        '殴打', '施暴', '暴力', '欺凌',
        # 负面事件（增强）
        '索赔', '争吵', '打架', '斗殴', '事故', '灾难', '火灾', '爆炸',
        '地震', '洪水', '台风', '暴雨', '伤亡', '死伤', '受伤',
        '被拖离', '被带走', '被捕', '被抓', '被拘',
        # 技术负面（新增）
        '宕机', '崩溃', '故障', '断网', '卡顿', '延迟', 'bug', '漏洞',
        '停服', '维护', '修复', '补偿',
        # 抄袭/造假类（新增）
        '抄袭', '实锤', '重罚', '处罚', '开除', '辞退',
        '造假', '欺诈', '骗局', '曝光', '查封', '立案', '罚款',
        '抓捕', '被捕', '拘留', '起诉', '诉讼',
        # 其他负面
        '恶化', '衰退', '萎缩', '低迷', '疲软', '乏力', '警告', '警惕',
        '质疑', '否认', '反驳',
        # 国际关系
        '示弱', '妥协', '退让', '屈服', '低头', '认输', '服软',
        '挑衅', '威胁', '恐吓', '制裁', '封锁', '打压',
        '侵犯', '干涉', '入侵', '占领', '吞并',
        # 辱骂/争议类
        '侮辱', '辱骂', '诋毁', '贬低', '羞辱', '蔑视', '鄙视',
        '像狗', '垃圾', '无耻', '可耻', '卑劣', '恶劣', '肮脏',
        '骗子', '欺诈', '虚假', '伪造', '盗版', '侵权',
        '痛批', '炮轰', '怒斥', '谴责', '声讨',
        # 被扒/旧账类
        '被扒', '旧账', '扒出', '翻旧账', '黑历史', '丑闻',
        '惹众怒', '引众怒', '激怒', '愤怒', '不满',
        '投诉', '举报', '曝光', '爆料',
    }

    NEGATION_WORDS = {
        '不', '没', '无', '非', '未', '别', '勿', '莫',
        '没有', '不是', '不再', '并非', '绝不', '决不',
        '毫不', '毫无', '未能', '未曾', '从未',
    }

    # ==================== 中性事件（扩展）====================
    NEUTRAL_EVENTS = {
        # 个人事件
        '再婚', '订婚', '结婚', '生子', '生日', '退休', '履新',
        '任职', '卸任', '访华', '会晤', '会谈', '通话',
        # 政策/法规
        '发布', '宣布', '公布', '出台', '印发', '施行',
        '召开', '举行', '举办', '开幕', '闭幕', '启动', '揭牌',
        '新规', '新政', '政策', '法规', '条例', '办法',
        '标准', '规范', '指南', '意见', '通知',
        '公积金', '住房', '贷款', '利率', '调整', '优化',
        # 签证/旅游
        '签证', '十年签', '免签', '落地签', '旅游', '出行',
        '开放', '放宽', '便利', '通行',
        # 天气/预警（新增）
        '预警', '冰雹', '暴雨', '雷电', '大风', '寒潮', '降温',
        '高温', '干旱', '台风', '洪水',
        # 产品/科技
        '发布', '上线', '更新', '升级', '版本', '功能',
        '评测', '体验', '试用', '内测', '公测',
        # 会议/活动
        '会议', '论坛', '峰会', '座谈会', '研讨会',
        '活动', '庆典', '仪式', '展览',
        # 疑问句特征
        '如何看待', '如何评价', '为什么', '怎样',
    }


    # ==================== 正则模式 ====================
    PATTERNS = {
        # 强负面
        'strong_negative': re.compile(r'(侮辱|辱骂|像狗|垃圾|无耻|可耻|卑劣|恶劣|肮脏|骗子|欺诈|虚假|伪造|盗版|侵权|痛批|炮轰|怒斥|谴责|声讨)'),
        'death': re.compile(r'(去世|逝世|猝死|心梗|遇难|牺牲)'),
        'weakness': re.compile(r'(示弱|妥协|退让|屈服|低头|认输|服软)'),
        # 否定正面
        'negate_positive': re.compile(r'(不再|无法|未能|难以|很难|几乎没有|很少)(?:\w{0,10})(?:突破|增长|领先|成功|进步|利好)'),
        # 正面肯定
        'confirm_positive': re.compile(r'(成功|顺利|圆满)(?:\w{0,10})(?:完成|实现|达成|交付|通过)'),
        # 新增：正面教程/推荐模式
        'positive_tutorial': re.compile(r'(别再|不要|别)(?:裸用|傻用|乱用|硬用).*?(?:拉满|翻倍|提升|必备|神器|效率|干货)'),
        'positive_guide': re.compile(r'(教程|指南|攻略|亲测|实测|推荐|分享).*?(?:拉满|翻倍|提升|必备|神器|效率|干货)'),
        'positive_combo': re.compile(r'(Skills|MCP|工具|技巧).*?(?:拉满|翻倍|必备|神器|效率)'),
    }

    def __init__(self):
        if not HAS_SNOWNLP:
            raise ImportError("请先安装 snownlp: pip install snownlp")

        self.data_cleaner = DataCleaner()
        self.project_root = Path(__file__).resolve().parent.parent
        self.output_dir = self.project_root / 'output'
        self.sentiment_dir = self.output_dir / 'sentiment'
        self.sentiment_dir.mkdir(parents=True, exist_ok=True)

    def is_question(self, text: str) -> bool:
        if text.endswith('？') or text.endswith('?'):
            return True
        question_words = ['如何', '怎样', '为什么', '怎么', '哪些', '什么', '吗', '呢', '如何看待', '如何评价']
        for qw in question_words:
            if qw in text:
                return True
        return False

    def has_negation(self, text: str, phrase: str) -> bool:
        idx = text.find(phrase)
        if idx == -1:
            return False
        prefix = text[max(0, idx-8):idx]
        for neg in self.NEGATION_WORDS:
            if neg in prefix:
                return True
        return False

    def pattern_match(self, text: str) -> Optional[Tuple[float, str]]:
        # 先检查正面教程模式（优先级高，避免被其他模式误判）
        if self.PATTERNS['positive_tutorial'].search(text):
            return 0.85, "positive_tutorial"
        if self.PATTERNS['positive_guide'].search(text):
            return 0.80, "positive_guide"
        if self.PATTERNS['positive_combo'].search(text):
            return 0.78, "positive_combo"
        
        # 强负面
        if self.PATTERNS['strong_negative'].search(text):
            return 0.05, "strong_negative"
        if self.PATTERNS['death'].search(text):
            return 0.05, "death_pattern"
        if self.PATTERNS['weakness'].search(text):
            return 0.30, "weakness_pattern"
        if self.PATTERNS['negate_positive'].search(text):
            return 0.35, "negate_positive_pattern"
        if self.PATTERNS['confirm_positive'].search(text):
            return 0.75, "confirm_positive_pattern"
        return None

    def event_neutral(self, text: str) -> bool:
        for event in self.NEUTRAL_EVENTS:
            if event in text:
                return True
        return False

    def sentiment_score(self, text: str) -> Tuple[float, str]:
        # 1. 疑问句 -> 中性
        if self.is_question(text):
            return 0.50, "question"

        # 2. 模式匹配
        pattern_result = self.pattern_match(text)
        if pattern_result:
            return pattern_result

        # 3. 中性事件 -> 中性
        if self.event_neutral(text):
            return 0.50, "neutral_event"

        # 4. SnowNLP 基础分
        s = SnowNLP(text)
        snow_score = s.sentiments

        # 5. 词典统计
        pos_count = 0
        neg_count = 0
        for word in self.POSITIVE_WORDS:
            if word in text:
                if self.has_negation(text, word):
                    neg_count += 1
                else:
                    pos_count += 1
        for word in self.NEGATIVE_WORDS:
            if word in text:
                if self.has_negation(text, word):
                    pos_count += 1
                else:
                    neg_count += 1

        # 6. 词典倾向分
        if pos_count + neg_count > 0:
            lexicon_score = pos_count / (pos_count + neg_count)
            final_score = snow_score * 0.3 + lexicon_score * 0.7
        else:
            final_score = snow_score

        # 7. 特殊调整
        if neg_count > pos_count:
            final_score = min(final_score, 0.35)
        if pos_count > 0 and neg_count == 0 and final_score < 0.5:
            final_score = min(0.65, final_score + 0.15)
        if neg_count > 0 and pos_count == 0 and final_score > 0.5:
            final_score = max(0.35, final_score - 0.15)

        final_score = max(0.0, min(1.0, final_score))
        return round(final_score, 4), "lexicon"

    def analyze_single(self, text: str) -> Dict[str, Any]:
        score, reason = self.sentiment_score(text)
        label = self.get_sentiment_label(score)
        icon = self.get_sentiment_icon(label)

        s = SnowNLP(text)
        keywords = s.keywords(limit=5)
        pos_found = [w for w in self.POSITIVE_WORDS if w in text]
        neg_found = [w for w in self.NEGATIVE_WORDS if w in text]

        return {
            'text': text,
            'sentiment_score': score,
            'sentiment_label': label,
            'sentiment_icon': icon,
            'analysis_reason': reason,
            'keywords': keywords,
            'positive_words': pos_found[:3],
            'negative_words': neg_found[:3],
            'length': len(text)
        }

    def get_sentiment_label(self, score: float) -> str:
        if score < 0.4:
            return 'negative'
        elif score < 0.6:
            return 'neutral'
        else:
            return 'positive'

    def get_sentiment_icon(self, label: str) -> str:
        icons = {'positive': '😊', 'neutral': '😐', 'negative': '😞'}
        return icons.get(label, '😐')

    def analyze_batch(self, items: List[Dict]) -> List[Dict]:
        print(f"[处理] 开始情感分析，共 {len(items)} 条数据")
        results = []
        stats = {'positive': 0, 'neutral': 0, 'negative': 0}
        reason_stats = Counter()

        for item in items:
            title = item.get('title', '')
            if not title:
                continue
            analysis = self.analyze_single(title)

            stats[analysis['sentiment_label']] += 1
            reason_stats[analysis['analysis_reason']] += 1

            enhanced = item.copy()
            enhanced.update({
                'sentiment_score': analysis['sentiment_score'],
                'sentiment_label': analysis['sentiment_label'],
                'sentiment_icon': analysis['sentiment_icon'],
                'analysis_reason': analysis['analysis_reason'],
                'sentiment_keywords': analysis['keywords'],
                'positive_words': analysis['positive_words'],
                'negative_words': analysis['negative_words'],
            })
            results.append(enhanced)

        print(f"[处理] 完成情感分析，共 {len(results)} 条")
        print(f"[统计] 正面: {stats['positive']} | 中性: {stats['neutral']} | 负面: {stats['negative']}")
        print(f"[统计] 分析依据: {dict(reason_stats)}")

        print("\n【情感分析示例】")
        for i, item in enumerate(results[:10], 1):
            label = item['sentiment_label']
            icon = item['sentiment_icon']
            score = item['sentiment_score']
            reason = item['analysis_reason']
            title = item['title'][:45] + '...' if len(item['title']) > 45 else item['title']
            print(f"  {i}. {icon} [{label}:{score:.3f}] ({reason}) {title}")

        return results

    def get_sentiment_statistics(self, items: List[Dict]) -> Dict[str, Any]:
        if not items:
            return {}

        counts = Counter()
        scores = []
        reasons = Counter()
        for item in items:
            label = item.get('sentiment_label', 'neutral')
            score = item.get('sentiment_score', 0.5)
            reason = item.get('analysis_reason', 'unknown')
            counts[label] += 1
            scores.append(score)
            reasons[reason] += 1

        total = len(items)
        avg_score = sum(scores) / total

        positive_items = [i for i in items if i.get('sentiment_label') == 'positive']
        negative_items = [i for i in items if i.get('sentiment_label') == 'negative']
        top_pos = sorted(positive_items, key=lambda x: x.get('sentiment_score', 0), reverse=True)[:3] if positive_items else []
        top_neg = sorted(negative_items, key=lambda x: x.get('sentiment_score', 1))[:3] if negative_items else []

        return {
            'total': total,
            'sentiment_distribution': {
                'positive': counts.get('positive', 0),
                'neutral': counts.get('neutral', 0),
                'negative': counts.get('negative', 0)
            },
            'positive_ratio': counts.get('positive', 0) / total if total else 0,
            'neutral_ratio': counts.get('neutral', 0) / total if total else 0,
            'negative_ratio': counts.get('negative', 0) / total if total else 0,
            'average_sentiment_score': round(avg_score, 4),
            'reason_distribution': dict(reasons),
            'top_positive': [{'title': i['title'][:50], 'score': i['sentiment_score']} for i in top_pos],
            'top_negative': [{'title': i['title'][:50], 'score': i['sentiment_score']} for i in top_neg]
        }

    def print_sentiment_report(self, items: List[Dict], title: str = "情感分析报告"):
        stats = self.get_sentiment_statistics(items)

        print(f"\n{'='*70}")
        print(f" {title}")
        print(f"{'='*70}")
        print(f"\n【情感分布统计】")
        print(f"  总数据量: {stats['total']} 条")
        print(f"  😊 正面: {stats['sentiment_distribution']['positive']} 条 ({stats['positive_ratio']*100:.1f}%)")
        print(f"  😐 中性: {stats['sentiment_distribution']['neutral']} 条 ({stats['neutral_ratio']*100:.1f}%)")
        print(f"  😞 负面: {stats['sentiment_distribution']['negative']} 条 ({stats['negative_ratio']*100:.1f}%)")
        print(f"  平均情感分: {stats['average_sentiment_score']:.4f}")

        print(f"\n【分析依据分布】")
        for reason, cnt in stats.get('reason_distribution', {}).items():
            print(f"  {reason}: {cnt} 条")

        print(f"\n【情感分布可视化】")
        print("-" * 70)
        pos_bar = int(stats['positive_ratio'] * 40)
        neu_bar = int(stats['neutral_ratio'] * 40)
        neg_bar = int(stats['negative_ratio'] * 40)
        print(f"  😊 正面: {'█' * pos_bar} {stats['positive_ratio']*100:.1f}%")
        print(f"  😐 中性: {'█' * neu_bar} {stats['neutral_ratio']*100:.1f}%")
        print(f"  😞 负面: {'█' * neg_bar} {stats['negative_ratio']*100:.1f}%")

        if stats['top_positive']:
            print(f"\n【最正面示例 TOP 3】")
            for i, it in enumerate(stats['top_positive'], 1):
                print(f"  {i}. [{it['score']:.3f}] {it['title']}")
        if stats['top_negative']:
            print(f"\n【最负面示例 TOP 3】")
            for i, it in enumerate(stats['top_negative'], 1):
                print(f"  {i}. [{it['score']:.3f}] {it['title']}")
        print(f"\n{'='*70}")

    def analyze_from_database(self, category: str = 'common', limit: int = 30) -> Dict[str, Any]:
        print(f"\n{'='*70}")
        print(f" 从数据库读取 {category} 类数据进行情感分析")
        print(f"{'='*70}")

        rows = get_latest_data(category, limit)
        if not rows:
            print(f"[错误] 数据库中没有 {category} 类数据")
            return {'items': [], 'statistics': {}}

        print(f"[加载] 读取 {len(rows)} 条数据")

        items = []
        for row in rows:
            items.append({
                'title': row['title'],
                'url': row['url'],
                'raw_weight': row['normalized_score'],
                'timestamp': row['crawl_time']
            })

        analyzed = self.analyze_batch(items)
        self.print_sentiment_report(analyzed, f"情感分析报告 - {category}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.sentiment_dir / f'sentiment_{category}_{timestamp}.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analyzed, f, ensure_ascii=False, indent=2)
        print(f"\n[保存] 情感分析结果已保存至: {output_path}")

        return {
            'items': analyzed,
            'statistics': self.get_sentiment_statistics(analyzed),
            'output_path': str(output_path)
        }

    def analyze_both(self):
        print(f"\n{'='*70}")
        print(f" {self.PROJECT_NAME} - 情感分析（数据库版）")
        print(f"{'='*70}")

        results = {}
        print(f"\n{'─'*70}")
        print("【综合类情感分析】")
        print(f"{'─'*70}")
        results['common'] = self.analyze_from_database('common', 30)

        print(f"\n{'─'*70}")
        print("【科技类情感分析】")
        print(f"{'─'*70}")
        results['tech'] = self.analyze_from_database('tech', 10)

        print(f"\n{'='*70}")
        print("[完成] 情感分析完成")
        print(f"{'='*70}")
        return results


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='情感分析器')
    parser.add_argument('--category', choices=['common', 'tech'], help='指定分析类型')
    args = parser.parse_args()

    analyzer = SentimentAnalyzer()

    if args.category:
        result = analyzer.analyze_from_database(args.category)
        stats = result['statistics']
        print(f"\n📊 分析结果摘要:")
        print(f"   {args.category}: {stats['total']} 条")
        print(f"   正面: {stats['sentiment_distribution']['positive']}条")
        print(f"   中性: {stats['sentiment_distribution']['neutral']}条")
        print(f"   负面: {stats['sentiment_distribution']['negative']}条")
        print(f"   平均分: {stats['average_sentiment_score']:.3f}")
    else:
        results = analyzer.analyze_both()
        print(f"\n📊 分析结果摘要:")
        for cat in ('common', 'tech'):
            if cat in results:
                s = results[cat]['statistics']
                print(f"   {cat}: {s['total']}条 | 正:{s['sentiment_distribution']['positive']} 中:{s['sentiment_distribution']['neutral']} 负:{s['sentiment_distribution']['negative']} | 均分:{s['average_sentiment_score']:.3f}")