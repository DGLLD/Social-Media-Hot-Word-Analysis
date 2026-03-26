#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
数据清洗模块（保留全部数据版）

功能：
1. 解析原始txt文件（每三行为一组）
2. 不截断数据，保留所有原始数据
3. 记录来源文件，便于后续分离处理
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
    数据清洗器（保留全部数据版）
    """
    
    PROJECT_NAME = "社交媒体热点词分析项目"
    
    def __init__(self, stopwords_path: str = None):
        """
        初始化清洗器
        
        Args:
            stopwords_path: 停用词表文件路径
        """
        # 获取项目根目录
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 加载停用词表
        self.stopwords = self._load_stopwords(stopwords_path)
        print(f"[初始化] 加载停用词: {len(self.stopwords)} 个")
        
        # 初始化jieba分词器
        self._init_jieba()
        
        print(f"[初始化] {self.PROJECT_NAME} - 数据清洗模块（保留全部数据版）")
    
    def _load_stopwords(self, stopwords_path: Optional[str] = None) -> set:
        """加载停用词表"""
        stopwords_set = set()
        
        if stopwords_path is None:
            stopwords_path = os.path.join(self.project_root, 'config', 'stopwords.txt')
        
        if os.path.exists(stopwords_path):
            with open(stopwords_path, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith('#'):
                        stopwords_set.add(word)
            print(f"[加载] 从 {os.path.basename(stopwords_path)} 加载停用词")
        else:
            # 内置默认停用词
            default_stopwords = [
                '的', '了', '是', '在', '和', '与', '或', '等', '有', '被', '把',
                '就', '都', '也', '还', '要', '会', '能', '可以', '可能',
                '这', '那', '之', '其', '于', '为', '以', '所', '不', '而',
                '吗', '呢', '吧', '啊', '哦', '嗯', '哈', '呀', '哟', '哎',
                '什么', '怎么', '为什么', '如何', '哪个', '哪些', '谁', '何时', '何处'
            ]
            stopwords_set.update(default_stopwords)
            print(f"[加载] 使用内置停用词: {len(stopwords_set)} 个")
        
        return stopwords_set
    
    def _init_jieba(self):
        """初始化jieba分词器"""
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
        """对标题进行分词"""
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
    
    def clean_file(self, file_path: str, timestamp: str = None) -> List[Dict[str, Any]]:
        """清洗单个文件（不截断，保留所有数据）"""
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 解析文件
        raw_items = self.parse_file(file_path)
        file_name = os.path.basename(file_path)
        print(f"[清洗] 解析 {file_name}: 共 {len(raw_items)} 条原始数据")
        
        # 按原始权重排序（权重越小排名越高）
        sorted_items = sorted(raw_items, key=lambda x: x['raw_weight'])
        
        # 确定来源类型
        source_type = 'tech' if '科技' in file_name else 'general'
        
        # 处理所有数据（不截断）
        cleaned_items = []
        total = len(sorted_items)
        
        for idx, item in enumerate(sorted_items):
            rank = idx + 1
            rank_score = (total - rank + 1) / total * 100
            
            words, word_count = self.tokenize_title(item['title'])
            
            date_part = timestamp[:10].replace('-', '')
            item_id = f"{date_part}_{source_type}_{idx:04d}"
            
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
        
        print(f"[清洗] 完成清洗: 共 {len(cleaned_items)} 条数据（全部保留）")
        return cleaned_items
    
    def clean_multiple_files(self, file_paths: List[str], timestamp: str = None) -> List[Dict[str, Any]]:
        """清洗多个文件并合并（不截断）"""
        all_items = []
        for file_path in file_paths:
            items = self.clean_file(file_path, timestamp)
            all_items.extend(items)
        
        print(f"\n[清洗] 总计清洗 {len(all_items)} 条数据，来自 {len(file_paths)} 个文件")
        
        # 按原始权重排序（全局排序，越小越热）
        all_items.sort(key=lambda x: x['raw_weight'])
        
        # 更新全局排名
        for idx, item in enumerate(all_items):
            item['global_rank'] = idx + 1
        
        print(f"[清洗] 保留全部 {len(all_items)} 条数据（未截断）")
        
        return all_items
    
    def save_cleaned_data(self, items: List[Dict], output_path: str):
        """保存清洗后的数据"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        
        print(f"[清洗] 数据已保存至: {output_path}")


# ==================== 主程序入口 ====================
if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    raw_dir = os.path.join(project_root, 'data', 'raw')
    processed_dir = os.path.join(project_root, 'data', 'processed')
    
    # 获取所有txt文件
    file_paths = []
    if os.path.exists(raw_dir):
        for filename in os.listdir(raw_dir):
            if filename.endswith('.txt'):
                file_paths.append(os.path.join(raw_dir, filename))
    
    if not file_paths:
        print("[错误] 未找到数据文件")
        exit(1)
    
    print(f"[信息] 发现 {len(file_paths)} 个数据文件")
    for fp in file_paths:
        print(f"       - {os.path.basename(fp)}")
    
    # 初始化清洗器
    cleaner = DataCleaner()
    
    # 清洗数据
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cleaned_items = cleaner.clean_multiple_files(file_paths, timestamp)
    
    # 保存结果
    output_path = os.path.join(processed_dir, f'cleaned_data_{datetime.now().strftime("%Y%m%d")}.json')
    cleaner.save_cleaned_data(cleaned_items, output_path)
    
    # 打印统计
    print(f"\n{'='*60}")
    print(f"清洗完成统计")
    print(f"{'='*60}")
    
    # 按来源类型统计
    general_count = len([i for i in cleaned_items if i.get('source_type') == 'general'])
    tech_count = len([i for i in cleaned_items if i.get('source_type') == 'tech'])
    
    print(f"综合热榜数据: {general_count} 条")
    print(f"科技热榜数据: {tech_count} 条")
    print(f"总计: {len(cleaned_items)} 条")
    print(f"{'='*60}")