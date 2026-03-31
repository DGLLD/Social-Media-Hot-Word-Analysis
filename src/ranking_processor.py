#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
排行处理器模块（支持数据库读取）

功能：
1. 从数据库读取综合热榜和科技热榜数据
2. 计算综合热度分
3. 生成综合热榜排行（前30条）和科技热榜排行（前10条）
4. 保存排名结果到 output/rankings/
5. 生成对应的词云图（文件名包含类别标识）

使用已有模块：
- data_cleaner: 数据清洗和分词
- ranking_engine: 排名计算

作者: 毕业实习项目组
创建时间: 2026-03-27
修改时间: 2026-03-28
"""

import os
import json
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 导入模块
try:
    from src.data_cleaner import DataCleaner
    from src.ranking_engine import RankingEngine
    from src.wordcloud_generator import WordCloudGenerator
except ImportError:
    from data_cleaner import DataCleaner
    from ranking_engine import RankingEngine
    from wordcloud_generator import WordCloudGenerator


class RankingProcessor:
    """
    排行处理器
    从数据库读取数据，生成综合排行和科技排行，并生成对应词云
    """
    
    PROJECT_NAME = "社交媒体热点词分析项目"
    
    # 显示条数配置
    GENERAL_TOP_N = 30   # 综合热榜显示前30条
    TECH_TOP_N = 10       # 科技热榜显示前10条
    
    def __init__(self):
        """初始化排行处理器"""
        # 初始化子模块
        self.data_cleaner = DataCleaner()
        self.ranking_engine = RankingEngine()
        self.wordcloud_generator = WordCloudGenerator()
        
        # 项目根目录
        self.project_root = Path(__file__).resolve().parent.parent
        self.output_dir = self.project_root / 'output'
        self.rankings_dir = self.output_dir / 'rankings'
        self.wordclouds_dir = self.output_dir / 'wordclouds'
        
        # 确保输出目录存在
        self._ensure_directories()
        
        print(f"[初始化] {self.PROJECT_NAME} - 排行处理器（数据库版）")
    
    def _ensure_directories(self):
        """确保输出目录存在"""
        self.rankings_dir.mkdir(parents=True, exist_ok=True)
        self.wordclouds_dir.mkdir(parents=True, exist_ok=True)
    
    def _ensure_directory(self, dir_path: str) -> bool:
        """确保目录存在"""
        try:
            path = Path(dir_path)
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"[警告] 目录创建失败: {e}")
            return False
    
    def load_and_clean_data(self, category: str = 'common', limit: int = 50) -> List[Dict]:
        """
        从数据库加载并清洗数据
        
        Args:
            category: 'common' 或 'tech'
            limit: 返回条数
            
        Returns:
            清洗后的数据列表
        """
        print(f"[加载] 从数据库读取 {category} 类数据...")
        
        # 从数据库读取并清洗
        cleaned_items = self.data_cleaner.clean_from_database(category, limit)
        
        if not cleaned_items:
            print(f"[警告] 未找到 {category} 类数据")
            return []
        
        print(f"[加载] 成功加载 {len(cleaned_items)} 条数据")
        return cleaned_items
    
    def process_rankings(self, items: List[Dict], name: str) -> List[Dict]:
        """
        处理排名计算
        
        Args:
            items: 清洗后的数据列表
            name: 名称（用于日志）
            
        Returns:
            排名后的数据列表
        """
        if not items:
            print(f"[跳过] {name}数据为空，跳过排名计算")
            return []
        
        print(f"\n[处理] 计算{name}排名...")
        
        # 使用 ranking_engine 计算排名
        ranked_items = self.ranking_engine.process_cleaned_data(items)
        
        return ranked_items
    
    def generate_wordcloud(self, items: List[Dict], category_name: str) -> Dict:
        """
        为指定数据生成词云
        
        Args:
            items: 数据列表
            category_name: 类别名称 'general' 或 'tech'
            
        Returns:
            词云结果字典
        """
        if not items:
            print(f"[跳过] {category_name}数据为空，跳过词云生成")
            return {}
        
        print(f"\n[处理] 生成{category_name}词云...")
        
        # 生成词云，传入类别标识
        result = self.wordcloud_generator.generate_from_cleaned_data(
            items, str(self.wordclouds_dir), category=category_name
        )
        
        return result
    
    def save_ranking_result(self, items: List[Dict], name: str) -> Optional[str]:
        """
        保存排名结果
        
        Args:
            items: 排名后的数据列表
            name: 名称（用于文件名）
            
        Returns:
            保存的文件路径
        """
        if not items:
            print(f"[跳过] {name}数据为空，跳过保存")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.rankings_dir / f'ranking_{name}_{timestamp}.json'
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"[保存] {name}排名已保存: {output_path.name}")
            return str(output_path)
        except Exception as e:
            print(f"[错误] 保存失败: {e}")
            # 备选：保存到当前目录
            fallback_path = Path(f'ranking_{name}_{timestamp}.json')
            with open(fallback_path, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"[备选] 已保存到: {fallback_path}")
            return str(fallback_path)
    
    def print_ranking_report(self, items: List[Dict], name: str, top_n: int = 15):
        """
        打印排行报告
        
        Args:
            items: 排名后的数据列表
            name: 名称
            top_n: 显示前N条
        """
        if not items:
            print(f"[跳过] {name}数据为空，无法生成报告")
            return
        
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
    
    def run(self, category: str = None):
        """
        执行完整处理流程
        
        Args:
            category: 指定处理类型，None表示全部处理，'general'或'tech'
        """
        print(f"\n{'='*70}")
        print(f" {self.PROJECT_NAME} - 排行处理（数据库版）")
        print(f"{'='*70}")
        
        results = {}
        
        # 处理综合热榜
        if category is None or category == 'general':
            print(f"\n{'─'*70}")
            print("【综合热榜排行】")
            print(f"{'─'*70}")
            
            # 加载综合类数据（前30条）
            general_items = self.load_and_clean_data('common', self.GENERAL_TOP_N)
            
            if general_items:
                # 计算排名
                general_ranked = self.process_rankings(general_items, "综合热榜")
                # 保存结果
                general_path = self.save_ranking_result(general_ranked, "general")
                # 打印报告
                self.print_ranking_report(general_ranked, "综合热榜", top_n=15)
                # 生成词云（传入类别标识 'general'）
                general_wordcloud = self.generate_wordcloud(general_ranked, "general")
                
                results['general'] = {
                    'items': general_ranked,
                    'count': len(general_ranked),
                    'path': general_path,
                    'wordcloud': general_wordcloud
                }
            else:
                print("[警告] 综合热榜无数据")
        
        # 处理科技热榜
        if category is None or category == 'tech':
            print(f"\n{'─'*70}")
            print("【科技热榜排行】")
            print(f"{'─'*70}")
            
            # 加载科技类数据（前10条）
            tech_items = self.load_and_clean_data('tech', self.TECH_TOP_N)
            
            if tech_items:
                # 计算排名
                tech_ranked = self.process_rankings(tech_items, "科技热榜")
                # 保存结果
                tech_path = self.save_ranking_result(tech_ranked, "tech")
                # 打印报告
                self.print_ranking_report(tech_ranked, "科技热榜", top_n=15)
                # 生成词云（传入类别标识 'tech'）
                tech_wordcloud = self.generate_wordcloud(tech_ranked, "tech")
                
                results['tech'] = {
                    'items': tech_ranked,
                    'count': len(tech_ranked),
                    'path': tech_path,
                    'wordcloud': tech_wordcloud
                }
            else:
                print("[警告] 科技热榜无数据")
        
        print(f"\n{'='*70}")
        print("[完成] 排行处理完成")
        if 'general' in results:
            print(f"  综合热榜: {results['general']['count']} 条数据")
        if 'tech' in results:
            print(f"  科技热榜: {results['tech']['count']} 条数据")
        print(f"{'='*70}")
        
        return results


# ==================== 主程序入口 ====================
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='排行处理器')
    parser.add_argument('--category', choices=['general', 'tech'], 
                        help='指定处理类型，不指定则处理全部')
    args = parser.parse_args()
    
    # 初始化处理器
    processor = RankingProcessor()
    
    # 运行
    results = processor.run(category=args.category)
    
    # 打印简要结果
    if results:
        print("\n📊 处理结果摘要:")
        for name, data in results.items():
            print(f"   {name}: {data['count']} 条数据")
            if data['path']:
                print(f"      排名文件: {Path(data['path']).name}")
            if data.get('wordcloud') and data['wordcloud'].get('output_path'):
                print(f"      词云文件: {Path(data['wordcloud']['output_path']).name}")