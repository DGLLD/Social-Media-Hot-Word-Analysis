#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
词云生成模块

功能：
1. 基于清洗后的数据生成词云图
2. 使用高频关键词绘制可视化词云
3. 支持保存为图片文件
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import Counter

# 尝试导入词云库，如果没有则提示安装
try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # 使用非交互式后端，避免GUI问题
    HAS_WORDCLOUD = True
except ImportError:
    HAS_WORDCLOUD = False
    print("[警告] 未安装 wordcloud 库，请运行: pip install wordcloud matplotlib")


class WordCloudGenerator:
    """
    词云生成器
    基于清洗数据中的分词结果生成词云
    """
    
    # 项目名称
    PROJECT_NAME = "社交媒体热点词分析项目"
    
    # 词云配置
    DEFAULT_CONFIG = {
        'width': 800,
        'height': 600,
        'background_color': 'white',
        'max_words': 100,
        'colormap': 'viridis',
        'font_path': None,
        'min_font_size': 10,
        'max_font_size': 80,
        'relative_scaling': 0.5
    }
    
    def __init__(self, config: Dict = None):
        """初始化词云生成器"""
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        
        # 设置中文字体
        self._setup_font()
        
        print(f"[初始化] {self.PROJECT_NAME} - 词云生成模块")
        print(f"[初始化] 词云尺寸: {self.config['width']}x{self.config['height']}")
    
    def _setup_font(self):
        """设置中文字体路径"""
        if self.config.get('font_path'):
            return
        
        # Windows常见中文字体路径
        font_paths = [
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simsun.ttc',
            'C:/Windows/Fonts/simkai.ttf',
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                self.config['font_path'] = path
                print(f"[字体] 使用字体: {os.path.basename(path)}")
                return
        
        print("[字体] 未找到中文字体，词云中文可能显示为方框")
    
    def get_word_freq(self, cleaned_items: List[Dict]) -> List[Tuple[str, int]]:
        """从清洗数据中统计词频"""
        word_freq = Counter()
        
        # 额外停用词
        extra_stopwords = {
            '情况', '第一', '时间', '发现', '导致', '要求', '预言', '跑马',
            '处于', '以来', '时期', '年度', '征文', '处于', '以来', '时期'
        }
        
        for item in cleaned_items:
            words = item.get('words', [])
            for word in words:
                if len(word) <= 1:
                    continue
                if word.isdigit():
                    continue
                if word in extra_stopwords:
                    continue
                word_freq[word] += 1
        
        return word_freq.most_common()
    
    def generate_wordcloud(self, word_freq: List[Tuple[str, int]], 
                          output_path: str) -> Any:
        """生成词云图并保存"""
        if not HAS_WORDCLOUD:
            print("[错误] 请先安装 wordcloud 库")
            return None
        
        if not word_freq:
            print("[错误] 词频数据为空")
            return None
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
                print(f"[创建] 创建目录: {output_dir}")
            except Exception as e:
                print(f"[错误] 无法创建目录: {e}")
                # 使用当前目录
                output_path = os.path.basename(output_path)
                print(f"[备选] 保存到当前目录: {output_path}")
        
        # 转换为字典
        freq_dict = dict(word_freq)
        
        # 创建词云对象
        wc = WordCloud(
            width=self.config['width'],
            height=self.config['height'],
            background_color=self.config['background_color'],
            max_words=self.config['max_words'],
            colormap=self.config['colormap'],
            font_path=self.config['font_path'],
            min_font_size=self.config['min_font_size'],
            max_font_size=self.config['max_font_size'],
            relative_scaling=self.config['relative_scaling']
        )
        
        # 生成词云
        wc.generate_from_frequencies(freq_dict)
        
        # 保存图片
        try:
            wc.to_file(output_path)
            print(f"[保存] 词云图已保存至: {output_path}")
        except Exception as e:
            print(f"[错误] 保存图片失败: {e}")
            # 尝试保存到当前目录
            fallback_path = f"wordcloud_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            wc.to_file(fallback_path)
            print(f"[备选] 已保存到: {fallback_path}")
            output_path = fallback_path
        
        return wc
    
    def generate_from_cleaned_data(self, cleaned_items: List[Dict],
                                   output_dir: str = None) -> Dict[str, Any]:
        """从清洗数据生成词云"""
        print(f"[处理] 开始生成词云，共 {len(cleaned_items)} 条热点数据")
        
        # 1. 统计词频
        word_freq = self.get_word_freq(cleaned_items)
        print(f"[统计] 共 {len(word_freq)} 个不同的词")
        
        # 2. 显示Top20高频词
        print(f"\n【词云高频词 Top 20】")
        print("-" * 50)
        for i, (word, freq) in enumerate(word_freq[:20], 1):
            bar_length = min(20, freq * 6)
            bar = "█" * bar_length if bar_length > 0 else "░"
            print(f"{i:2d}. {word:<12} : {freq:3} 次 {bar}")
        
        # 3. 生成输出路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_dir:
            # 确保输出目录存在
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception:
                output_dir = None
        
        if output_dir:
            output_path = os.path.join(output_dir, f'wordcloud_{timestamp}.png')
        else:
            output_path = f'wordcloud_{timestamp}.png'
        
        # 4. 生成词云
        wc = self.generate_wordcloud(word_freq, output_path)
        
        # 5. 返回结果
        return {
            'word_freq': word_freq,
            'total_words': len(word_freq),
            'top_words': word_freq[:20],
            'output_path': output_path if output_path else None,
            'config': self.config
        }
    
    def save_word_freq(self, word_freq: List[Tuple[str, int]], output_path: str):
        """保存词频数据为JSON"""
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
        except Exception:
            output_path = os.path.basename(output_path)
        
        data = [{'word': word, 'freq': freq} for word, freq in word_freq]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[保存] 词频数据已保存至: {output_path}")


# ==================== 主程序入口 ====================
if __name__ == '__main__':
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # 文件路径
    processed_dir = os.path.join(project_root, 'data', 'processed')
    output_dir = os.path.join(project_root, 'output', 'wordclouds')
    
    # 查找最新的清洗数据文件
    cleaned_files = []
    if os.path.exists(processed_dir):
        for filename in os.listdir(processed_dir):
            if filename.startswith('cleaned_data_') and filename.endswith('.json'):
                cleaned_files.append(os.path.join(processed_dir, filename))
    
    if not cleaned_files:
        print("[错误] 未找到清洗后的数据文件，请先运行 data_cleaner.py")
        exit(1)
    
    # 使用最新的文件
    latest_file = max(cleaned_files, key=os.path.getmtime)
    print(f"[信息] 加载清洗数据: {os.path.basename(latest_file)}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        cleaned_items = json.load(f)
    
    print(f"[信息] 加载 {len(cleaned_items)} 条数据")
    
    # 初始化词云生成器
    generator = WordCloudGenerator()
    
    # 生成词云
    result = generator.generate_from_cleaned_data(cleaned_items, output_dir)
    
    # 保存词频数据
    freq_output = os.path.join(output_dir, f'word_freq_{datetime.now().strftime("%Y%m%d")}.json')
    generator.save_word_freq(result['word_freq'], freq_output)
    
    print(f"\n[完成] 词云生成完成")
    print(f"  总词数: {result['total_words']}")
    print(f"  Top词: {result['top_words'][:5]}")
    print(f"  图片路径: {result['output_path']}")