#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
SnowNLP情感分析模块（词典分级+语境词优化版）

优化内容：
1. 情感词分级（强/中/弱），赋予不同权重
2. 语境词增强（竟是、太厉害了、大神等）
3. 正面/负面计数加权，提高正面识别准确率
4. 保留原有规则（疑问句、中性事件、正则模式）
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

    # ==================== 分级情感词典 ====================
    # 强正面词（权重3）
    STRONG_POSITIVE = {
        '夺冠', '金牌', '胜利', '凯旋', '辉煌', '卓越', '震撼', '奇迹',
        '里程碑', '历史性', '重大突破', '世界第一', '破纪录', '冠军',
        '满分', '金牌', '状元', '榜首',
    }
    
    # 中等正面词（权重2）
    MEDIUM_POSITIVE = {
        '突破', '大涨', '利好', '新高', '创新', '领先', '增长', '成功',
        '优秀', '进步', '发展', '提升', '改善', '好转', '回暖', '爆发',
        '崛起', '腾飞', '热销', '抢购', '涨停', '飙升', '暴涨', '猛涨',
        '里程碑', '首次', '首创', '开源', '发布', '上线', '推出', '亮相',
        '攻克', '治愈', '康复', '痊愈', '救活', '挽救', '祝贺', '恭喜',
        '点赞', '支持', '称赞', '好评', '认可', '肯定', '致敬', '缅怀',
        '感动', '温暖', '振奋', '回升', '复苏', '企稳', '向好', '红利',
        '幸福', '快乐', '开心', '高兴', '激动', '兴奋', '骄傲', '自豪',
        '期待', '向往', '希望', '信心', '信任',
    }
    
    # 弱正面词（权重1）
    WEAK_POSITIVE = {
        '教程', '指南', '攻略', '亲测', '实测', '推荐', '神器', '必备',
        '工具', '技巧', '干货', '经验', '分享', '总结', '心得',
        '效率', '拉满', '翻倍', '加速', '优化', '提升',
        '不错', '挺好', '可以', '还行', '值得', '满意',
    }
    
    # 强负面词（权重3）
    STRONG_NEGATIVE = {
        '去世', '逝世', '猝死', '心梗', '遇难', '牺牲', '身亡', '遗体',
        '命案', '凶杀', '杀人', '杀害', '谋杀', '血案', '惨案', '悲剧',
        '崩盘', '破产', '倒闭', '灾难', '爆炸', '火灾', '事故', '车祸',
        '战争', '袭击', '轰炸', '空袭', '导弹',
    }
    
    # 中等负面词（权重2）
    MEDIUM_NEGATIVE = {
        '暴跌', '崩盘', '危机', '下跌', '下滑', '亏损', '负债', '裁员',
        '降薪', '违约', '失信', '违规', '违法', '争议', '风险', '调查',
        '纠纷', '冲突', '对抗', '紧张', '示威', '抗议', '暴乱', '骚乱',
        '关押', '监禁', '囚禁', '炼狱', '地狱', '折磨', '虐待', '酷刑',
        '殴打', '施暴', '暴力', '欺凌', '索赔', '争吵', '打架', '斗殴',
        '地震', '洪水', '台风', '暴雨', '恶化', '衰退', '萎缩', '低迷',
        '疲软', '乏力', '警告', '警惕', '质疑', '否认', '反驳',
    }
    
    # 弱负面词（权重1）
    WEAK_NEGATIVE = {
        '示弱', '妥协', '退让', '屈服', '低头', '认输', '服软',
        '挑衅', '威胁', '恐吓', '制裁', '封锁', '打压', '侵犯', '干涉',
        '侮辱', '辱骂', '诋毁', '贬低', '羞辱', '蔑视', '鄙视',
        '像狗', '垃圾', '无耻', '可耻', '卑劣', '恶劣', '肮脏',
        '骗子', '欺诈', '虚假', '伪造', '盗版', '侵权', '痛批', '炮轰',
        '怒斥', '谴责', '声讨', '被扒', '旧账', '扒出', '惹众怒', '引众怒',
        '激怒', '愤怒', '不满', '投诉', '举报', '曝光', '被查',
    }
    
    # ==================== 语境增强词 ====================
    # 正面语境词（增强正面倾向）
    POSITIVE_CONTEXT = {
        '竟是', '原来', '太厉害了', '神操作', '大神', '牛', '厉害',
        '太牛了', '真牛', '真厉害', '佩服', '惊艳', '没想到',
        '竟然', '居然', '原来如此', '终于', '成功了', '太棒了',
        '厉害了', '我的天', '神了', '绝了',
    }
    
    # 负面语境词（增强负面倾向）
    NEGATIVE_CONTEXT = {
        '竟然', '居然', '没想到', '可怕', '恐怖', '吓人', '震惊',
        '无语', '离谱', '过分', '过分了', '太过了', '令人发指',
    }
    
    # 特殊组合规则（曝光+大神 = 正面）
    SPECIAL_COMBOS = [
        (['曝光', '被扒'], ['大神', '牛', '厉害', '神操作', '竟是'], 0.85, 'positive_boost'),
        (['去世', '逝世'], ['哀悼', '缅怀', '致敬'], 0.35, 'negative_boost'),  # 悼念但仍是负面
    ]

    NEGATION_WORDS = {
        '不', '没', '无', '非', '未', '别', '勿', '莫',
        '没有', '不是', '不再', '并非', '绝不', '决不',
        '毫不', '毫无', '未能', '未曾', '从未',
    }

    NEUTRAL_EVENTS = {
        '再婚', '订婚', '结婚', '生子', '生日', '退休', '履新',
        '任职', '卸任', '访华', '会晤', '会谈', '通话',
        '发布', '宣布', '公布', '出台', '印发', '施行',
        '召开', '举行', '举办', '开幕', '闭幕', '启动', '揭牌',
        '新规', '新政', '政策', '法规', '条例', '办法',
        '标准', '规范', '指南', '意见', '通知', '公积金', '住房', '贷款',
        '利率', '调整', '优化', '签证', '免签', '旅游', '出行', '开放',
        '放宽', '便利', '通行', '预警', '冰雹', '暴雨', '雷电', '大风',
        '寒潮', '降温', '高温', '干旱', '台风', '洪水',
    }

    PATTERNS = {
        'strong_negative': re.compile(r'(去世|逝世|猝死|心梗|遇难|牺牲|身亡|遗体|命案|凶杀|杀人|杀害|谋杀|血案|惨案|悲剧|崩盘|破产|倒闭|灾难|爆炸|火灾|车祸|事故|战争|袭击|轰炸|空袭|导弹)'),
        'death': re.compile(r'(去世|逝世|猝死|心梗|遇难|牺牲|身亡|遗体|失联)'),
        'accident': re.compile(r'(爆炸|火灾|车祸|事故|伤亡|死伤|受伤|坍塌|坠落)'),
        'weakness': re.compile(r'(示弱|妥协|退让|屈服|低头|认输|服软)'),
        'positive_tutorial': re.compile(r'(别再|不要|别)(?:裸用|傻用|乱用|硬用).*?(?:拉满|翻倍|提升|必备|神器|效率|干货)'),
        'positive_guide': re.compile(r'(教程|指南|攻略|亲测|实测|推荐|分享).*?(?:拉满|翻倍|提升|必备|神器|效率|干货)'),
        'positive_combo': re.compile(r'(Skills|MCP|工具|技巧).*?(?:拉满|翻倍|必备|神器|效率)'),
        'champion': re.compile(r'(夺冠|金牌|胜利|凯旋)'),
    }

    # 强制中性词库
    FORCED_NEUTRAL_WORDS = {
        '总书记', '主席', '总理', '习近平', '李克强', '领导人', '党和国家领导人',
        '国务院', '中共中央', '全国人大', '全国政协', '中央军委', '中宣部', '中组部',
        '二十大', '两会', '政府工作报告', '五年规划', '十四五', '中国梦', '复兴',
    }

    def __init__(self):
        if not HAS_SNOWNLP:
            raise ImportError("请先安装 snownlp: pip install snownlp")

        self.data_cleaner = DataCleaner()
        self.project_root = Path(__file__).resolve().parent.parent
        self.output_dir = self.project_root / 'output'
        self.sentiment_dir = self.output_dir / 'sentiment'
        self.sentiment_dir.mkdir(parents=True, exist_ok=True)

        print(f"[初始化] {self.PROJECT_NAME} - 情感分析模块（词典分级+语境词版）")
        print(f"[初始化] 强正面词: {len(self.STRONG_POSITIVE)}个")
        print(f"[初始化] 中正面词: {len(self.MEDIUM_POSITIVE)}个")
        print(f"[初始化] 弱正面词: {len(self.WEAK_POSITIVE)}个")
        print(f"[初始化] 强负面词: {len(self.STRONG_NEGATIVE)}个")
        print(f"[初始化] 中负面词: {len(self.MEDIUM_NEGATIVE)}个")
        print(f"[初始化] 弱负面词: {len(self.WEAK_NEGATIVE)}个")
        print(f"[初始化] 正面语境词: {len(self.POSITIVE_CONTEXT)}个")
        print(f"[初始化] 负面语境词: {len(self.NEGATIVE_CONTEXT)}个")

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
        if self.PATTERNS['positive_tutorial'].search(text):
            return 0.85, "positive_tutorial"
        if self.PATTERNS['positive_guide'].search(text):
            return 0.80, "positive_guide"
        if self.PATTERNS['positive_combo'].search(text):
            return 0.78, "positive_combo"
        if self.PATTERNS['champion'].search(text):
            return 0.85, "champion"
        if self.PATTERNS['strong_negative'].search(text):
            return 0.05, "strong_negative"
        if self.PATTERNS['death'].search(text):
            return 0.05, "death_pattern"
        if self.PATTERNS['accident'].search(text):
            return 0.10, "accident_pattern"
        if self.PATTERNS['weakness'].search(text):
            return 0.30, "weakness_pattern"
        return None

    def event_neutral(self, text: str) -> bool:
        for event in self.NEUTRAL_EVENTS:
            if event in text:
                return True
        return False

    def should_force_neutral(self, text: str) -> bool:
        for word in self.FORCED_NEUTRAL_WORDS:
            if word in text:
                return True
        return False

    def check_special_combos(self, text: str) -> Optional[Tuple[float, str]]:
        """检查特殊组合规则"""
        for neg_words, pos_words, score, reason in self.SPECIAL_COMBOS:
            has_neg = any(w in text for w in neg_words)
            has_pos = any(w in text for w in pos_words)
            if has_neg and has_pos:
                return score, reason
        return None

    def calculate_lexicon_score(self, text: str) -> Tuple[float, int, int]:
        """
        计算分级词典得分
        返回: (得分, 正面计数, 负面计数)
        """
        pos_count = 0
        neg_count = 0
        
        # 强正面词（权重3）
        for word in self.STRONG_POSITIVE:
            if word in text:
                if self.has_negation(text, word):
                    neg_count += 3
                else:
                    pos_count += 3
        
        # 中等正面词（权重2）
        for word in self.MEDIUM_POSITIVE:
            if word in text:
                if self.has_negation(text, word):
                    neg_count += 2
                else:
                    pos_count += 2
        
        # 弱正面词（权重1）
        for word in self.WEAK_POSITIVE:
            if word in text:
                if self.has_negation(text, word):
                    neg_count += 1
                else:
                    pos_count += 1
        
        # 强负面词（权重3）
        for word in self.STRONG_NEGATIVE:
            if word in text:
                if self.has_negation(text, word):
                    pos_count += 3
                else:
                    neg_count += 3
        
        # 中等负面词（权重2）
        for word in self.MEDIUM_NEGATIVE:
            if word in text:
                if self.has_negation(text, word):
                    pos_count += 2
                else:
                    neg_count += 2
        
        # 弱负面词（权重1）
        for word in self.WEAK_NEGATIVE:
            if word in text:
                if self.has_negation(text, word):
                    pos_count += 1
                else:
                    neg_count += 1
        
        # 正面语境增强
        for word in self.POSITIVE_CONTEXT:
            if word in text:
                pos_count += 2
        
        # 负面语境增强
        for word in self.NEGATIVE_CONTEXT:
            if word in text:
                neg_count += 2
        
        # 计算得分
        if pos_count + neg_count > 0:
            lexicon_score = pos_count / (pos_count + neg_count)
        else:
            lexicon_score = 0.5
        
        return lexicon_score, pos_count, neg_count

    def sentiment_score(self, text: str) -> Tuple[float, str]:
        # 0. 强制中性词检查
        if self.should_force_neutral(text):
            return 0.50, "forced_neutral"

        # 1. 疑问句 -> 中性
        if self.is_question(text):
            return 0.50, "question"

        # 2. 特殊组合规则
        special_result = self.check_special_combos(text)
        if special_result:
            return special_result

        # 3. 模式匹配
        pattern_result = self.pattern_match(text)
        if pattern_result:
            return pattern_result

        # 4. 中性事件 -> 中性
        if self.event_neutral(text):
            return 0.50, "neutral_event"

        # 5. SnowNLP 基础分
        s = SnowNLP(text)
        snow_score = s.sentiments

        # 6. 分级词典得分
        lexicon_score, pos_count, neg_count = self.calculate_lexicon_score(text)

        # 7. 混合得分（词典权重提高到70%）
        final_score = snow_score * 0.3 + lexicon_score * 0.7

        # 8. 边界调整
        final_score = max(0.0, min(1.0, final_score))
        
        return round(final_score, 4), "lexicon"

    def analyze_single(self, text: str) -> Dict[str, Any]:
        score, reason = self.sentiment_score(text)
        label = self.get_sentiment_label(score)
        icon = self.get_sentiment_icon(label)

        s = SnowNLP(text)
        keywords = s.keywords(limit=5)
        
        # 统计情感词（用于调试）
        pos_found = []
        neg_found = []
        
        for word in self.STRONG_POSITIVE | self.MEDIUM_POSITIVE | self.WEAK_POSITIVE:
            if word in text:
                pos_found.append(word)
        for word in self.STRONG_NEGATIVE | self.MEDIUM_NEGATIVE | self.WEAK_NEGATIVE:
            if word in text:
                neg_found.append(word)
        
        # 语境词也加入显示
        context_words = [w for w in self.POSITIVE_CONTEXT if w in text] + \
                        [w for w in self.NEGATIVE_CONTEXT if w in text]
        
        return {
            'text': text,
            'sentiment_score': score,
            'sentiment_label': label,
            'sentiment_icon': icon,
            'analysis_reason': reason,
            'keywords': keywords,
            'positive_words': list(set(pos_found))[:3],
            'negative_words': list(set(neg_found))[:3],
            'context_words': context_words[:3],
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
                'context_words': analysis.get('context_words', []),
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