#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
词云生成模块（水平显示版）

优化内容：
1. 所有词水平显示，易于阅读
2. 填满整个画布，无空白区域
3. 显示高频词 Top 30
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import Counter

try:
    from wordcloud import WordCloud, STOPWORDS
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    HAS_WORDCLOUD = True
except ImportError:
    HAS_WORDCLOUD = False
    print("[警告] 请安装: pip install wordcloud matplotlib numpy")


class WordCloudGenerator:
    """
    词云生成器（水平显示版）
    所有词水平显示，填满画布
    """
    
    PROJECT_NAME = "社交媒体热点词分析项目"
    
    # 配置（全部水平显示）
    DEFAULT_CONFIG = {
        'width': 800,
        'height': 600,
        'background_color': 'white',
        'max_words': 30,
        'colormap': 'plasma',
        'font_path': None,
        'min_font_size': 14,
        'max_font_size': 70,
        'relative_scaling': 0.7,
        'prefer_horizontal': 1.0,      # 1.0 = 全部水平显示
        'margin': 5,
        'random_state': 42,
        'scale': 2,
        'contour_width': 1,
        'contour_color': '#f0f0f0'
    }
    
    # 扩展停用词表
    EXTRA_STOPWORDS = {
        # 疑问词
        '什么', '怎么', '为什么', '如何', '哪些', '谁', '吗', '呢', '吧',
        '哪里', '何时', '何处', '咋', '干嘛', '为啥',
        # 虚词
        '的', '了', '是', '在', '和', '与', '或', '等', '有', '被', '把',
        '就', '都', '也', '还', '要', '会', '能', '可以', '可能',
        '这', '那', '之', '其', '于', '为', '以', '所', '不', '而',
        # 代词
        '我', '你', '他', '她', '它', '我们', '你们', '他们', '她们', '它们',
        '自己', '别人', '大家', '人家',
        # 连词
        '但是', '然而', '虽然', '因为', '所以', '因此', '于是', '那么',
        '以及', '并且', '而且', '或者', '还是', '要么', '不仅', '不但',
        # 程度词
        '很', '太', '更', '最', '极', '非常', '特别', '尤其', '比较', '相当',
        # 时间词
        '今天', '昨天', '明天', '现在', '过去', '未来', '之前', '之后',
        '已经', '正在', '将会', '即将',
        # 无意义词
        '这是', '东西', '这么', '那么', '这样', '那样', '一样', '而已',
        '的话', '来说', '而言', '来讲', '来看', '总之', '实际上',
        '情况', '第一', '时间', '发现', '导致', '要求', '预言', '跑马',
        '处于', '以来', '时期', '年度', '征文', '背后', '原理', '国家'
    }
    
    def __init__(self, config: Dict = None):
        """初始化词云生成器"""
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        
        self._setup_font()
        self._setup_stopwords()
        
        print(f"[初始化] {self.PROJECT_NAME} - 词云生成模块")
        print(f"[初始化] 词云尺寸: {self.config['width']}x{self.config['height']}")
        print(f"[初始化] 显示词数: Top {self.config['max_words']}")
        print(f"[初始化] 文字方向: 全部水平 (prefer_horizontal=1.0)")
        print(f"[初始化] 配色方案: {self.config['colormap']}")
    
    def _setup_font(self):
        """设置中文字体"""
        if self.config.get('font_path'):
            return
        
        # Windows常见中文字体路径（按优先级排序）
        font_paths = [
            'C:/Windows/Fonts/msyh.ttc',         # 微软雅黑（首选）
            'C:/Windows/Fonts/simhei.ttf',       # 黑体
            'C:/Windows/Fonts/simsun.ttc',       # 宋体
            'C:/Windows/Fonts/simkai.ttf',       # 楷体
            'C:/Windows/Fonts/SourceHanSansSC-Regular.otf',  # 思源黑体
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                self.config['font_path'] = path
                font_name = os.path.basename(path).replace('.ttf', '').replace('.ttc', '')
                print(f"[字体] 使用字体: {font_name}")
                return
        
        print("[字体] 未找到中文字体，将使用默认字体（可能显示异常）")
    
    def _setup_stopwords(self):
        """设置停用词"""
        self.stopwords = set(STOPWORDS) if HAS_WORDCLOUD else set()
        self.stopwords.update(self.EXTRA_STOPWORDS)
    
    def get_top_words(self, cleaned_items: List[Dict], top_n: int = 30) -> List[Tuple[str, int]]:
        """获取高频词 Top N"""
        word_freq = Counter()
        
        for item in cleaned_items:
            words = item.get('words', [])
            for word in words:
                if len(word) <= 1:
                    continue
                if word.isdigit():
                    continue
                if word in self.stopwords:
                    continue
                word_freq[word] += 1
        
        return word_freq.most_common(top_n)
    
    def generate_wordcloud(self, word_freq: List[Tuple[str, int]], 
                          output_path: str) -> Any:
        """生成词云图（全部水平，填满画布）"""
        if not HAS_WORDCLOUD:
            print("[错误] 请安装 wordcloud 库")
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
                print(f"[警告] 目录创建失败: {e}")
        
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
            relative_scaling=self.config['relative_scaling'],
            prefer_horizontal=self.config['prefer_horizontal'],  # 关键：水平显示
            margin=self.config['margin'],
            random_state=self.config['random_state'],
            scale=self.config['scale'],
            stopwords=self.stopwords
        )
        
        # 生成词云
        wc.generate_from_frequencies(freq_dict)
        
        # 保存图片
        try:
            wc.to_file(output_path)
            print(f"[保存] 词云图已保存至: {output_path}")
        except Exception as e:
            print(f"[错误] 保存失败: {e}")
        
        return wc
    
    def generate_from_cleaned_data(self, cleaned_items: List[Dict],
                                   output_dir: str = None) -> Dict[str, Any]:
        """从清洗数据生成词云"""
        print(f"[处理] 开始生成词云，共 {len(cleaned_items)} 条热点数据")
        
        # 获取高频词 Top 30
        top_n = self.config['max_words']
        word_freq = self.get_top_words(cleaned_items, top_n)
        
        # 打印高频词列表
        print(f"\n{'='*70}")
        print(f"【词云高频词 Top {len(word_freq)}】（全部水平显示）")
        print(f"{'='*70}")
        print(f"{'排名':<4} {'关键词':<15} {'频次':<6} {'热度占比'}")
        print("-" * 70)
        
        total_freq = sum(freq for _, freq in word_freq)
        for i, (word, freq) in enumerate(word_freq, 1):
            percent = freq / total_freq * 100 if total_freq > 0 else 0
            bar_len = int(percent * 1.2)
            bar = "█" * bar_len if bar_len > 0 else "░"
            print(f"{i:<4} {word:<15} {freq:<6} {percent:>5.1f}% {bar}")
        
        # 确保输出目录存在
        if output_dir:
            try:
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                    print(f"[创建] 创建目录: {output_dir}")
            except Exception as e:
                print(f"[警告] 目录创建失败，使用当前目录: {e}")
                output_dir = '.'
        else:
            output_dir = '.'
        
        # 生成输出路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f'wordcloud_{timestamp}.png')
        freq_output = os.path.join(output_dir, f'word_freq_{timestamp}.json')
        
        # 生成词云
        wc = self.generate_wordcloud(word_freq, output_path)
        
        # 保存词频数据
        try:
            with open(freq_output, 'w', encoding='utf-8') as f:
                data = [{'rank': i+1, 'word': word, 'freq': freq} 
                        for i, (word, freq) in enumerate(word_freq)]
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[保存] 词频数据已保存至: {freq_output}")
        except Exception as e:
            print(f"[错误] 保存词频失败: {e}")
        
        return {
            'word_freq': word_freq,
            'total_words': len(word_freq),
            'top_words': word_freq,
            'output_path': output_path
        }


# ==================== 主程序入口 ====================
if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    processed_dir = os.path.join(project_root, 'data', 'processed')
    output_dir = os.path.join(project_root, 'output', 'wordclouds')
    
    # 查找最新的清洗数据文件
    cleaned_files = []
    if os.path.exists(processed_dir):
        for filename in os.listdir(processed_dir):
            if filename.startswith('cleaned_data_') and filename.endswith('.json'):
                cleaned_files.append(os.path.join(processed_dir, filename))
    
    if not cleaned_files:
        print("[错误] 未找到清洗后的数据文件")
        exit(1)
    
    latest_file = max(cleaned_files, key=os.path.getmtime)
    print(f"[信息] 加载清洗数据: {os.path.basename(latest_file)}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        cleaned_items = json.load(f)
    
    print(f"[信息] 加载 {len(cleaned_items)} 条数据")
    
    # 确保输出目录存在
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
    except Exception:
        pass
    
    # 初始化词云生成器
    generator = WordCloudGenerator()
    
    # 生成词云
    result = generator.generate_from_cleaned_data(cleaned_items, output_dir)
    
    print(f"\n{'='*70}")
    print(f"[完成] 词云生成完成")
    print(f"  总词数: {result['total_words']}")
    print(f"  Top 10: {[w for w, _ in result['top_words'][:10]]}")
    print(f"  图片路径: {result['output_path']}")
    print(f"{'='*70}")