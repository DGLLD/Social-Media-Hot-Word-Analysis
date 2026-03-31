#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
数据清洗模块（支持数据库读取）

功能：
1. 从 SQLite 数据库读取热榜数据
2. 对标题进行分词（jieba）
3. 过滤停用词
4. 输出统一格式的清洗数据（内存中，供后续模块使用）

数据来源：
- 优先从数据库读取（推荐）
- 兼容原有 txt 文件读取方式

作者: 毕业实习项目组
创建时间: 2026-03-27
"""

import os
import json
import re
import sys
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from collections import Counter

import jieba
import jieba.analyse

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 导入数据库连接模块
try:
    from src.db_connect import get_latest_data, get_db_stats
except ImportError:
    from db_connect import get_latest_data, get_db_stats


class DataCleaner:
    """
    数据清洗器
    支持从数据库读取和从文件读取
    """
    
    PROJECT_NAME = "社交媒体热点词分析项目"
    
    # 默认停用词（如果停用词文件不存在）
    DEFAULT_STOPWORDS = {
        '的', '了', '是', '在', '和', '与', '或', '等', '有', '被', '把',
        '就', '都', '也', '还', '要', '会', '能', '可以', '可能', '就',
        '这', '那', '之', '其', '于', '为', '以', '所', '不', '而',
        '吗', '呢', '吧', '啊', '哦', '嗯', '哈', '呀', '哟', '哎',
        '什么', '怎么', '为什么', '如何', '哪个', '哪些', '谁', '何时', '何处',
        '很', '太', '更', '最', '极', '非常', '特别', '尤其', '比较', '相当',
        '但是', '然而', '虽然', '因为', '所以', '因此', '于是', '那么',
        '以及', '并且', '而且', '或者', '还是', '要么', '不仅', '不但',
        '我', '你', '他', '她', '它', '我们', '你们', '他们', '她们', '它们',
        '今天', '昨天', '明天', '现在', '过去', '未来', '之前', '之后',
        '已经', '正在', '将会', '即将', '这是', '东西'
    }
    
    def __init__(self, stopwords_path: str = None):
        """
        初始化清洗器
        
        Args:
            stopwords_path: 停用词表文件路径
        """
        # 获取项目根目录
        self.project_root = Path(__file__).resolve().parent.parent
        
        # 加载停用词表
        self.stopwords = self._load_stopwords(stopwords_path)
        print(f"[初始化] 加载停用词: {len(self.stopwords)} 个")
        
        # 初始化jieba分词器
        self._init_jieba()
        
        print(f"[初始化] {self.PROJECT_NAME} - 数据清洗模块（支持数据库）")
    
    def _load_stopwords(self, stopwords_path: Optional[str] = None) -> set:
        """
        加载停用词表
        
        Args:
            stopwords_path: 停用词表文件路径
            
        Returns:
            停用词集合
        """
        stopwords_set = set()
        
        # 尝试从文件加载
        if stopwords_path is None:
            stopwords_path = self.project_root / 'config' / 'stopwords.txt'
        
        if stopwords_path.exists():
            with open(stopwords_path, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith('#'):
                        stopwords_set.add(word)
            print(f"[加载] 从 {stopwords_path.name} 加载停用词")
        else:
            # 使用默认停用词
            stopwords_set.update(self.DEFAULT_STOPWORDS)
            print(f"[加载] 使用内置停用词: {len(stopwords_set)} 个")
        
        return stopwords_set
    
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
            '姆巴佩', '席琳迪翁', '马斯克', '特朗普', '普京', '罗技',
            '孟子义', '李昀锐', '白敬亭', '杨笠', '林俊杰',
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
    
    def tokenize_title(self, title: str) -> Tuple[List[str], int]:
        """
        对标题进行分词
        
        Args:
            title: 标题文本
            
        Returns:
            (分词列表, 词数)
        """
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
    
    # ==================== 从数据库读取 ====================
    
    def load_from_database(self, category: str = 'common', limit: int = 50) -> List[Dict[str, Any]]:
        """
        从数据库读取最新数据
        
        Args:
            category: 'common' 或 'tech'
            limit: 返回条数（综合类建议 30，科技类建议 10）
            
        Returns:
            清洗前的数据列表，每条包含 raw_weight, title, url, timestamp
        """
        print(f"[数据库] 读取 {category} 类数据，限制 {limit} 条")
        
        rows = get_latest_data(category, limit)
        
        if not rows:
            print(f"[警告] 数据库中没有 {category} 类数据")
            return []
        
        items = []
        for row in rows:
            items.append({
                'raw_weight': row['normalized_score'],
                'title': row['title'],
                'url': row['url'],
                'timestamp': row['crawl_time']
            })
        
        print(f"[数据库] 成功读取 {len(items)} 条数据")
        return items
    
    def clean_from_database(self, category: str = 'common', limit: int = 50) -> List[Dict[str, Any]]:
        """
        从数据库读取并清洗数据
        
        Args:
            category: 'common' 或 'tech'
            limit: 返回条数
            
        Returns:
            清洗后的数据列表
        """
        # 1. 从数据库读取
        raw_items = self.load_from_database(category, limit)
        
        if not raw_items:
            return []
        
        # 2. 清洗数据
        cleaned_items = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for idx, item in enumerate(raw_items):
            words, word_count = self.tokenize_title(item['title'])
            
            cleaned_item = {
                'id': f"{category}_{idx:04d}",
                'title': item['title'],
                'url': item['url'],
                'raw_weight': item['raw_weight'],
                'timestamp': item['timestamp'] or timestamp,
                'words': words,
                'word_count': word_count,
                'length': len(item['title']),
                'source_type': category
            }
            cleaned_items.append(cleaned_item)
        
        print(f"[清洗] {category} 类清洗完成: {len(cleaned_items)} 条")
        return cleaned_items
    
    # ==================== 从文件读取（兼容旧版） ====================
    
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        解析单个txt文件
        
        文件格式：每三行为一组
        - 第1行：权重分数（0-1之间，越小排名越高/热度越高）
        - 第2行：标题文本
        - 第3行：URL链接
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的数据列表
        """
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
    
    def clean_from_file(self, file_path: str, timestamp: str = None) -> List[Dict[str, Any]]:
        """
        从文件读取并清洗数据（兼容旧版）
        
        Args:
            file_path: 文件路径
            timestamp: 采集时间戳
            
        Returns:
            清洗后的数据列表
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 1. 解析文件
        raw_items = self.parse_file(file_path)
        file_name = os.path.basename(file_path)
        print(f"[文件] 解析 {file_name}: 共 {len(raw_items)} 条原始数据")
        
        # 2. 按原始权重排序（权重越小排名越高）
        sorted_items = sorted(raw_items, key=lambda x: x['raw_weight'])
        
        # 3. 清洗数据
        cleaned_items = []
        total = len(sorted_items)
        
        for idx, item in enumerate(sorted_items):
            rank = idx + 1
            rank_score = (total - rank + 1) / total * 100
            
            words, word_count = self.tokenize_title(item['title'])
            
            date_part = timestamp[:10].replace('-', '')
            item_id = f"{date_part}_{idx:04d}"
            
            # 确定来源类型
            source_type = 'tech' if '科技' in file_name else 'general'
            
            cleaned_item = {
                'id': item_id,
                'title': item['title'],
                'url': item['url'],
                'source_file': file_name,
                'source_type': source_type,
                'raw_weight': item['raw_weight'],
                'rank': rank,
                'total_count': total,
                'rank_score': round(rank_score, 2),
                'timestamp': timestamp,
                'words': words,
                'word_count': word_count,
                'length': len(item['title'])
            }
            cleaned_items.append(cleaned_item)
        
        print(f"[文件] 完成清洗: {len(cleaned_items)} 条数据")
        return cleaned_items
    
    # ==================== 通用接口 ====================
    
    def clean(self, source: str = 'database', category: str = 'common', limit: int = 50) -> List[Dict[str, Any]]:
        """
        通用清洗接口
        
        Args:
            source: 'database' 或 'file'
            category: 'common' 或 'tech'（仅 database 模式有效）
            limit: 返回条数（仅 database 模式有效）
            
        Returns:
            清洗后的数据列表
        """
        if source == 'database':
            return self.clean_from_database(category, limit)
        else:
            # file 模式需要指定文件路径
            raise ValueError("file 模式需要指定 file_path 参数，请使用 clean_from_file 方法")
    
    def get_statistics(self, items: List[Dict]) -> Dict[str, Any]:
        """
        获取清洗数据的统计信息
        
        Args:
            items: 清洗后的数据列表
            
        Returns:
            统计信息字典
        """
        if not items:
            return {'total': 0}
        
        # 标题长度统计
        lengths = [item['length'] for item in items]
        
        # 词数统计
        word_counts = [item['word_count'] for item in items]
        
        # 词频统计
        word_freq = Counter()
        for item in items:
            for word in item['words']:
                word_freq[word] += 1
        
        top_words = word_freq.most_common(20)
        
        return {
            'total': len(items),
            'avg_length': sum(lengths) / len(lengths),
            'min_length': min(lengths),
            'max_length': max(lengths),
            'avg_word_count': sum(word_counts) / len(word_counts),
            'min_word_count': min(word_counts),
            'max_word_count': max(word_counts),
            'top_words': top_words
        }


# ==================== 主程序入口 ====================
if __name__ == '__main__':
    # 初始化清洗器
    cleaner = DataCleaner()
    
    print("\n" + "=" * 60)
    print("数据清洗模块测试")
    print("=" * 60)
    
    # 测试1：从数据库读取综合类数据
    print("\n1. 从数据库读取综合类数据（前30条）...")
    general_items = cleaner.clean_from_database('common', 30)
    
    if general_items:
        print(f"\n   综合类数据示例（前5条）:")
        for i, item in enumerate(general_items[:5], 1):
            print(f"   {i}. [{item['raw_weight']:.4f}] {item['title'][:50]}...")
            print(f"      分词: {item['words'][:5]}...")
    
    # 测试2：从数据库读取科技类数据
    print("\n2. 从数据库读取科技类数据（前10条）...")
    tech_items = cleaner.clean_from_database('tech', 10)
    
    if tech_items:
        print(f"\n   科技类数据示例（前5条）:")
        for i, item in enumerate(tech_items[:5], 1):
            print(f"   {i}. [{item['raw_weight']:.4f}] {item['title'][:50]}...")
            print(f"      分词: {item['words'][:5]}...")
    
    # 测试3：统计信息
    if general_items:
        print("\n3. 统计信息:")
        stats = cleaner.get_statistics(general_items)
        print(f"   总数据量: {stats['total']} 条")
        print(f"   平均标题长度: {stats['avg_length']:.1f} 字")
        print(f"   平均词数: {stats['avg_word_count']:.1f} 个")
        print(f"   Top 10 高频词: {[w for w, _ in stats['top_words'][:10]]}")
    
    # 测试4：数据库状态
    print("\n4. 数据库状态:")
    stats = get_db_stats()
    print(f"   综合类: {stats['common']['count']} 条，最后入库: {stats['common']['last_time']}")
    print(f"   科技类: {stats['tech']['count']} 条，最后入库: {stats['tech']['last_time']}")
    
    print("\n✅ 数据清洗模块测试完成")