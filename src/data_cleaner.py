#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
毕业实习（社交媒体热点词分析项目）
数据清洗模块（优化版）

功能：
1. 解析原始数据（支持文件或实时数据）
2. 使用哈工大停用词表 + 自定义停用词
3. 只保留前20热度的热点词
4. 输出统一JSON格式
5. 高频词统计 Top 20（用于词云）
"""

import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import jieba
import jieba.analyse


class DataCleaner:
    """
    数据清洗器（优化版）
    - 支持实时数据输入
    - 使用哈工大停用词表
    - 只保留前N热度的热点词
    - 高频词统计 Top 20
    """
    
    # 项目名称
    PROJECT_NAME = "毕业实习（社交媒体热点词分析项目）"
    
    # 默认只保留前N条热点（权重最小）
    DEFAULT_TOP_N = 20
    
    # 词云高频词数量
    WORDCLOUD_TOP_N = 20
    
    def __init__(self, 
                 stopwords_path: str = None,
                 category_path: str = None,
                 top_n: int = None):
        """
        初始化清洗器
        
        Args:
            stopwords_path: 停用词表文件路径
            category_path: 分类关键词文件路径
            top_n: 保留前N条热点，默认20
        """
        # 设置保留条数
        self.top_n = top_n or self.DEFAULT_TOP_N
        self.wordcloud_top_n = self.WORDCLOUD_TOP_N
        
        # 获取项目根目录
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 加载停用词表
        self.stopwords = self._load_stopwords(stopwords_path)
        print(f"[初始化] 加载停用词: {len(self.stopwords)} 个")
        
        # 加载分类关键词
        self.category_keywords = self._load_category_keywords(category_path)
        
        # 初始化jieba分词器
        self._init_jieba()
        
        print(f"[初始化] {self.PROJECT_NAME}")
        print(f"[初始化] 只保留前 {self.top_n} 条热点数据")
        print(f"[初始化] 词云高频词统计: Top {self.wordcloud_top_n}")
    
    def _load_stopwords(self, stopwords_path: Optional[str] = None) -> set:
        """
        加载停用词表
        优先级：指定路径 > config/stopwords.txt > 内置默认
        """
        stopwords_set = set()
        
        # 尝试从文件加载
        if stopwords_path is None:
            stopwords_path = os.path.join(self.project_root, 'config', 'stopwords.txt')
        
        if os.path.exists(stopwords_path):
            with open(stopwords_path, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith('#'):
                        stopwords_set.add(word)
            print(f"[加载] 从 {os.path.basename(stopwords_path)} 加载停用词")
        
        # 如果没有加载到任何词，使用内置默认
        if not stopwords_set:
            default_stopwords = [
                '的', '了', '是', '在', '和', '与', '或', '等', '有', '被', '把',
                '就', '都', '也', '还', '要', '会', '能', '可以', '可能', '就',
                '这', '那', '之', '其', '于', '为', '以', '所', '不', '而',
                '吗', '呢', '吧', '啊', '哦', '嗯', '哈', '呀', '哟', '哎',
                '什么', '怎么', '为什么', '如何', '哪个', '哪些', '谁', '何时', '何处',
                '很', '太', '更', '最', '极', '非常', '特别', '尤其', '比较', '相当',
                '但是', '然而', '虽然', '因为', '所以', '因此', '于是', '那么',
                '以及', '并且', '而且', '或者', '还是', '要么', '不仅', '不但',
                '我', '你', '他', '她', '它', '我们', '你们', '他们', '她们', '它们',
                '今天', '昨天', '明天', '现在', '过去', '未来', '之前', '之后'
            ]
            stopwords_set.update(default_stopwords)
            print(f"[加载] 使用内置停用词: {len(stopwords_set)} 个")
        
        return stopwords_set
    
    def _load_category_keywords(self, category_path: Optional[str] = None) -> Dict:
        """加载分类关键词库"""
        if category_path is None:
            category_path = os.path.join(self.project_root, 'config', 'category_keywords.json')
        
        if os.path.exists(category_path):
            with open(category_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {}
    
    def _init_jieba(self):
        """初始化jieba分词器，添加自定义词典"""
        custom_words = [
            # AI相关
            'OpenClaw', 'Claude', 'Meta', 'GPT', 'AI', 'Token', '词元',
            'Sora', 'OpenAI', 'DeepSeek', 'Claude Code', 'WebAssembly',
            '大模型', '人工智能', '机器学习', '深度学习', '人形机器人',
            # 人物
            '张雪峰', '周杰伦', '雷军', '余承东', '何刚', '黄仁勋',
            '王兴兴', '傅盛', '周鸿祎', '王自如', '朱伟', '张宇',
            '霍启刚', '郭晶晶', '郝蕾', '纪凌尘', '刘亦菲', '孔雪儿',
            '颜如晶', '宁艺卓', '张凌赫', '王俊凯', '金泰亨', '田柾国',
            '姆巴佩', '席琳迪翁', '马斯克', '特朗普', '普京',
            # 公司/产品
            '鸿蒙', '问界', '华为', '小米', '苹果', '腾讯', '阿里',
            '字节', '抖音', '微信', '美团', '京东', '百度', '知乎',
            '微博', '贴吧', '36氪', '虎嗅', 'IT之家', '掘金', '少数派',
            '峰学蔚来', 'OpenClaw', 'Claude', 'OpenAI', 'MiniMax',
            # 事件/疾病
            '心源性猝死', 'AED', '速效救心丸', '心梗', '高血压',
            '嘴唇发紫', '心脏不好', '跑步',
            # 综艺/影视
            '浪姐', '乘风破浪', '逐玉', '哈利波特', '生化危机',
            '白日提灯', '恋与深空', '开推', '太阳之子'
        ]
        
        for word in custom_words:
            jieba.add_word(word)
        
        jieba.setLogLevel(jieba.logging.INFO)
    
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """解析单个txt文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        lines = content.split('\n')
        items = []
        
        for i in range(0, len(lines), 3):
            if i + 2 >= len(lines):
                break
            
            weight_line = lines[i].strip()
            title_line = lines[i+1].strip()
            url_line = lines[i+2].strip()
            
            if not weight_line or not title_line or not url_line:
                continue
            
            try:
                weight = float(weight_line)
            except ValueError:
                continue
            
            items.append({
                'raw_weight': weight,
                'title': title_line,
                'url': url_line
            })
        
        return items
    
    def tokenize_title(self, title: str) -> Tuple[List[str], int]:
        """对标题进行分词（优化版）"""
        words = jieba.lcut(title)
        
        filtered_words = []
        for w in words:
            w = w.strip()
            if not w:
                continue
            if w in self.stopwords:
                continue
            if len(w) == 1 and not w.isalpha():
                continue
            if w.isdigit():
                continue
            if re.match(r'^[^\w\u4e00-\u9fa5]+$', w):
                continue
            filtered_words.append(w)
        
        return filtered_words, len(filtered_words)
    
    def clean_data(self, 
                   source_data: List[Dict], 
                   timestamp: str = None) -> List[Dict[str, Any]]:
        """清洗数据的统一入口"""
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sorted_data = sorted(source_data, key=lambda x: x['raw_weight'])
        top_data = sorted_data[:self.top_n]
        
        cleaned_items = []
        total = len(sorted_data)
        
        for idx, item in enumerate(top_data):
            actual_rank = sorted_data.index(item) + 1
            rank_score = (total - actual_rank + 1) / total * 100
            
            words, word_count = self.tokenize_title(item['title'])
            
            date_part = timestamp[:10].replace('-', '')
            item_id = f"{date_part}_{idx:04d}"
            
            cleaned_item = {
                'id': item_id,
                'title': item['title'],
                'url': item.get('url', ''),
                'raw_weight': item['raw_weight'],
                'rank': actual_rank,
                'total_count': total,
                'rank_score': round(rank_score, 2),
                'timestamp': timestamp,
                'words': words,
                'word_count': word_count,
                'length': len(item['title'])
            }
            cleaned_items.append(cleaned_item)
        
        return cleaned_items
    
    def clean_from_files(self, file_paths: List[str], timestamp: str = None) -> List[Dict[str, Any]]:
        """从文件清洗数据"""
        all_raw = []
        for file_path in file_paths:
            items = self.parse_file(file_path)
            all_raw.extend(items)
        
        return self.clean_data(all_raw, timestamp)
    
    def save_cleaned_data(self, items: List[Dict], output_path: str):
        """保存清洗后的数据"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        
        print(f"[清洗] 数据已保存至: {output_path}")
    
    def get_wordcloud_data(self, items: List[Dict]) -> List[Tuple[str, int]]:
        """
        获取词云数据（Top 20 高频词）
        供词云生成模块使用
        """
        word_freq = {}
        for item in items:
            for word in item['words']:
                if len(word) > 1 and not word.isdigit() and word not in self.stopwords:
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        # 返回 Top 20
        return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:self.wordcloud_top_n]
    
    def print_statistics(self, items: List[Dict]):
        """打印统计信息"""
        print("\n" + "="*70)
        print(f" {self.PROJECT_NAME}")
        print("="*70)
        
        print(f"\n【数据统计】")
        print(f"  总数据量: {len(items)} 条（前{self.top_n}热度热点）")
        
        weights = [item['raw_weight'] for item in items]
        print(f"\n【权重分布】")
        print(f"  最热权重: {min(weights):.4f}")
        print(f"  第{self.top_n}热权重: {max(weights):.4f}")
        print(f"  平均权重: {sum(weights)/len(weights):.4f}")
        
        lengths = [item['length'] for item in items]
        print(f"\n【标题长度】")
        print(f"  最短: {min(lengths)} 字")
        print(f"  最长: {max(lengths)} 字")
        print(f"  平均: {sum(lengths)/len(lengths):.1f} 字")
        
        word_counts = [item['word_count'] for item in items]
        print(f"\n【分词数量】")
        print(f"  最少: {min(word_counts)} 个词")
        print(f"  最多: {max(word_counts)} 个词")
        print(f"  平均: {sum(word_counts)/len(word_counts):.1f} 个词")
        
        print(f"\n【热点 TOP {len(items)}】")
        print("-" * 70)
        for i, item in enumerate(items[:self.top_n], 1):
            title_display = item['title'][:45] + '...' if len(item['title']) > 45 else item['title']
            print(f"{i:2d}. 权重={item['raw_weight']:.4f} | {title_display}")
        
        # 高频词统计 Top 20（用于词云）
        print(f"\n【词云高频词 Top {self.wordcloud_top_n}】（已过滤停用词）")
        print("-" * 70)
        
        wordcloud_data = self.get_wordcloud_data(items)
        max_freq = wordcloud_data[0][1] if wordcloud_data else 1
        
        for i, (word, freq) in enumerate(wordcloud_data, 1):
            # 可视化词频条（按比例显示）
            bar_length = int(freq / max_freq * 30)
            bar = "█" * bar_length if bar_length > 0 else "░"
            print(f"{i:2d}. {word:<12} : {freq:3} 次 {bar}")
        
        print("\n" + "="*70)
        print("[完成] 数据清洗完成，可用于后续分析模块")
        print("="*70)


# ==================== 主程序入口 ====================
if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    raw_dir = os.path.join(project_root, 'data', 'raw')
    processed_dir = os.path.join(project_root, 'data', 'processed')
    config_dir = os.path.join(project_root, 'config')
    
    os.makedirs(config_dir, exist_ok=True)
    
    # 检查停用词文件
    stopwords_path = os.path.join(config_dir, 'stopwords.txt')
    if not os.path.exists(stopwords_path):
        print(f"[提示] 停用词文件不存在: {stopwords_path}")
        print(f"[提示] 将使用内置停用词")
    
    # 获取所有txt文件
    file_paths = []
    if os.path.exists(raw_dir):
        for filename in os.listdir(raw_dir):
            if filename.endswith('.txt'):
                file_paths.append(os.path.join(raw_dir, filename))
    
    if not file_paths:
        print("[错误] 未找到数据文件，请将txt文件放入 data/raw/ 目录")
        exit(1)
    
    print(f"[信息] 发现 {len(file_paths)} 个数据文件:")
    for fp in file_paths:
        print(f"       - {os.path.basename(fp)}")
    
    # 初始化清洗器（Top20）
    cleaner = DataCleaner(top_n=20)
    
    # 清洗数据
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cleaned_items = cleaner.clean_from_files(file_paths, timestamp)
    
    # 保存结果
    output_path = os.path.join(processed_dir, f'cleaned_data_{datetime.now().strftime("%Y%m%d")}.json')
    cleaner.save_cleaned_data(cleaned_items, output_path)
    
    # 打印统计（含词云Top20）
    cleaner.print_statistics(cleaned_items)
    
    # 可选：单独导出词云数据
    wordcloud_data = cleaner.get_wordcloud_data(cleaned_items)
    wordcloud_output = os.path.join(processed_dir, f'wordcloud_data_{datetime.now().strftime("%Y%m%d")}.json')
    with open(wordcloud_output, 'w', encoding='utf-8') as f:
        json.dump(wordcloud_data, f, ensure_ascii=False, indent=2)
    print(f"\n[词云] 词云数据已保存至: {wordcloud_output}")