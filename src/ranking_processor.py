#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
排行处理器模块

功能：
1. 生成综合热点词排行（所有数据）
2. 生成科技热点词排行（仅科技热榜数据）
3. 分别为综合排行和科技排行生成词云

使用已有模块：
- ranking_engine: 排名计算
- wordcloud_generator: 词云生成
"""

import os
import json
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ranking_engine import RankingEngine
from src.wordcloud_generator import WordCloudGenerator


class RankingProcessor:
    """
    排行处理器
    生成综合排行和分类排行，并生成对应词云
    """
    
    PROJECT_NAME = "社交媒体热点词分析项目"
    
    # 分类关键词（用于识别科技类）
    TECH_KEYWORDS = [
        'AI', '大模型', 'OpenClaw', 'Claude', 'Meta', 'GPT', 'Token', '词元',
        'Sora', 'OpenAI', '鸿蒙', '华为', '小米', '苹果', '腾讯', '阿里',
        '字节', '芯片', '机器人', '算法', '数据', '智能', '云计算', '5G', '6G',
        '人工智能', '机器学习', '深度学习', '自动驾驶', 'WebAssembly', 'React', 'Vue',
        'Claude Code', 'Cursor', 'GitHub', 'Copilot', '编程', '前端', '后端',
        'OpenClaw', 'Claude', 'AI', '人工智能', '大模型', '机器人'
    ]
    
    def __init__(self, cleaned_data_path: str = None):
        """
        初始化排行处理器
        
        Args:
            cleaned_data_path: 清洗后的数据文件路径
        """
        self.cleaned_data_path = cleaned_data_path
        self.all_items = []
        self.tech_items = []
        
        # 初始化子模块
        self.ranking_engine = RankingEngine()
        self.wordcloud_generator = WordCloudGenerator()
        
        print(f"[初始化] {self.PROJECT_NAME} - 排行处理器")
    
    def load_data(self, data_path: str = None) -> List[Dict]:
        """
        加载清洗后的数据
        
        Args:
            data_path: 数据文件路径，默认使用初始化时的路径
            
        Returns:
            数据列表
        """
        path = data_path or self.cleaned_data_path
        if not path:
            raise ValueError("未指定数据文件路径")
        
        with open(path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        print(f"[加载] 读取 {len(items)} 条数据: {os.path.basename(path)}")
        return items
    
    def filter_tech_items(self, items: List[Dict]) -> List[Dict]:
        """
        筛选科技类热点
        
        筛选规则：
        1. 标题中包含科技关键词
        2. 或者分词结果中包含科技关键词
        
        Args:
            items: 所有数据列表
            
        Returns:
            科技类数据列表
        """
        tech_items = []
        
        for item in items:
            title = item.get('title', '')
            words = item.get('words', [])
            
            # 检查标题或分词中是否包含科技关键词
            is_tech = False
            for keyword in self.TECH_KEYWORDS:
                if keyword in title or keyword in words:
                    is_tech = True
                    break
            
            if is_tech:
                tech_items.append(item)
        
        print(f"[筛选] 科技类热点: {len(tech_items)} 条 (总数 {len(items)} 条)")
        
        # 打印科技类标题示例
        if tech_items:
            print(f"[示例] 科技类标题:")
            for i, item in enumerate(tech_items[:5], 1):
                title = item['title'][:50] + '...' if len(item['title']) > 50 else item['title']
                print(f"  {i}. {title}")
        
        return tech_items
    
    def process_rankings(self, items: List[Dict], name: str) -> List[Dict]:
        """
        处理排名计算
        
        Args:
            items: 数据列表
            name: 名称（用于日志）
            
        Returns:
            排名后的数据列表
        """
        print(f"\n[处理] 计算{name}排名...")
        
        # 使用 ranking_engine 计算排名
        ranked_items = self.ranking_engine.process_cleaned_data(items)
        
        return ranked_items
    
    def generate_wordcloud_for_items(self, items: List[Dict], 
                                     output_dir: str,
                                     name: str) -> Dict:
        """
        为指定数据生成词云
        
        Args:
            items: 数据列表
            output_dir: 输出目录
            name: 名称（用于文件名）
            
        Returns:
            词云结果字典
        """
        print(f"\n[处理] 生成{name}词云...")
        
        # 使用 wordcloud_generator 生成词云
        result = self.wordcloud_generator.generate_from_cleaned_data(items, output_dir)
        
        # 重命名输出文件（添加分类标识）
        if result.get('output_path'):
            old_path = result['output_path']
            dir_name = os.path.dirname(old_path)
            ext = os.path.splitext(old_path)[1]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_path = os.path.join(dir_name, f'wordcloud_{name}_{timestamp}{ext}')
            
            # 重命名文件
            if os.path.exists(old_path):
                try:
                    os.rename(old_path, new_path)
                    result['output_path'] = new_path
                    print(f"[重命名] 词云已重命名为: {os.path.basename(new_path)}")
                except Exception as e:
                    print(f"[警告] 重命名失败: {e}")
        
        return result
    
    def save_ranking_result(self, items: List[Dict], output_dir: str, name: str):
        """
        保存排名结果
        
        Args:
            items: 排名后的数据列表
            output_dir: 输出目录
            name: 名称（用于文件名）
        """
        # 修复目录创建问题
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                print(f"[创建] 创建目录: {output_dir}")
        except Exception as e:
            print(f"[警告] 目录创建失败: {e}")
            # 使用当前目录作为备选
            output_dir = '.'
            print(f"[备选] 使用当前目录")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f'ranking_{name}_{timestamp}.json')
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"[保存] {name}排名已保存: {os.path.basename(output_path)}")
        except Exception as e:
            print(f"[错误] 保存失败: {e}")
            # 备选：保存到当前目录
            fallback_path = f'ranking_{name}_{timestamp}.json'
            with open(fallback_path, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"[备选] 已保存到: {fallback_path}")
        
        return output_path
    
    def print_ranking_report(self, items: List[Dict], name: str, top_n: int = 10):
        """
        打印排行报告
        
        Args:
            items: 排名后的数据列表
            name: 名称
            top_n: 显示前N条
        """
        print(f"\n{'='*70}")
        print(f"【{name}热点排行 TOP {min(top_n, len(items))}】")
        print(f"{'='*70}")
        print(f"{'排名':<4} {'综合分':<8} {'权重':<8} {'标题'}")
        print("-" * 70)
        
        for i, item in enumerate(items[:top_n], 1):
            title = item.get('title', '')[:55]
            if len(item.get('title', '')) > 55:
                title += '...'
            print(f"{i:<4} {item.get('comprehensive_score', 0):<8.1f} "
                  f"{item.get('raw_weight', 0):<8.4f} {title}")
        
        # 分数统计
        scores = [item.get('comprehensive_score', 0) for item in items]
        if scores:
            print("-" * 70)
            print(f"统计: 最高 {max(scores):.1f} | 最低 {min(scores):.1f} | "
                  f"平均 {sum(scores)/len(scores):.1f} | 共{len(items)}条")
    
    def run(self, data_path: str = None, output_dir: str = None):
        """
        执行完整处理流程
        
        Args:
            data_path: 清洗数据文件路径
            output_dir: 输出目录
        """
        print(f"\n{'='*70}")
        print(f" {self.PROJECT_NAME} - 排行处理")
        print(f"{'='*70}")
        
        # 1. 加载数据
        items = self.load_data(data_path)
        
        # 2. 设置输出目录
        if output_dir is None:
            project_root = os.path.dirname(os.path.dirname(__file__))
            output_dir = os.path.join(project_root, 'output', 'rankings')
        
        # 3. 处理综合排行
        print(f"\n{'─'*70}")
        print("【综合热点排行】")
        print(f"{'─'*70}")
        
        all_ranked = self.process_rankings(items, "综合")
        self.save_ranking_result(all_ranked, output_dir, "all")
        self.print_ranking_report(all_ranked, "综合", top_n=15)
        
        # 4. 生成综合排行词云
        wordcloud_output_dir = os.path.join(os.path.dirname(output_dir), 'wordclouds')
        all_wordcloud = self.generate_wordcloud_for_items(
            all_ranked, wordcloud_output_dir, "all"
        )
        
        # 5. 筛选科技类数据
        tech_items = self.filter_tech_items(items)
        
        if tech_items:
            print(f"\n{'─'*70}")
            print("【科技热点排行】")
            print(f"{'─'*70}")
            
            # 6. 处理科技排行
            tech_ranked = self.process_rankings(tech_items, "科技")
            self.save_ranking_result(tech_ranked, output_dir, "tech")
            self.print_ranking_report(tech_ranked, "科技", top_n=15)
            
            # 7. 生成科技排行词云
            tech_wordcloud = self.generate_wordcloud_for_items(
                tech_ranked, wordcloud_output_dir, "tech"
            )
        else:
            print("[提示] 未找到科技类热点数据")
        
        print(f"\n{'='*70}")
        print("[完成] 排行处理完成")
        print(f"{'='*70}")


# ==================== 主程序入口 ====================
if __name__ == '__main__':
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # 文件路径
    processed_dir = os.path.join(project_root, 'data', 'processed')
    output_dir = os.path.join(project_root, 'output', 'rankings')
    
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
    print(f"[信息] 使用数据文件: {os.path.basename(latest_file)}")
    
    # 确保输出目录存在
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
    except Exception:
        pass
    
    # 初始化处理器并运行
    processor = RankingProcessor()
    processor.run(latest_file, output_dir)