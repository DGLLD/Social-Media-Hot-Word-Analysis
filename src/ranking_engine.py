#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
排名加权计算模块

功能：
1. 基于清洗数据的 raw_weight 直接进行排名
2. raw_weight 越小表示热度越高（权重值越低排名越高）
3. 计算综合热度分（0-100分制）
4. 为后续排行生成和趋势分析提供数据基础
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


class RankingEngine:
    """
    排名加权计算引擎
    
    核心逻辑：
    - raw_weight 越小 = 热度越高
    - 直接基于 raw_weight 排序，无需识别平台
    - 计算排名分数和综合热度分
    """
    
    # 项目名称
    PROJECT_NAME = "社交媒体热点词分析项目"
    
    # 热度分数计算公式参数
    DECAY_FACTOR = 0.85  # 衰减因子，越小头部集中度越高
    
    def __init__(self, decay_factor: float = None):
        """
        初始化排名加权引擎
        
        Args:
            decay_factor: 衰减因子，默认0.85
        """
        if decay_factor is not None:
            self.DECAY_FACTOR = decay_factor
        
        print(f"[初始化] {self.PROJECT_NAME} - 排名加权计算模块")
        print(f"[初始化] 衰减因子: {self.DECAY_FACTOR}")
    
    def rank_to_score(self, rank: int, total: int) -> float:
        """
        将排名转换为分数
        
        使用指数衰减公式：
        score = 100 × (decay_factor ^ (rank - 1))
        
        Args:
            rank: 排名（1为最热）
            total: 总条数（用于边界处理）
            
        Returns:
            排名分数（0-100）
        """
        if rank <= 0:
            return 0
        
        # 指数衰减
        score = 100 * (self.DECAY_FACTOR ** (rank - 1))
        
        # 确保分数在合理范围内
        return max(0, min(100, round(score, 2)))
    
    def weight_to_rank(self, raw_weight: float, all_weights: List[float]) -> int:
        """
        根据原始权重计算排名
        
        raw_weight 越小，排名越高（1为最热）
        
        Args:
            raw_weight: 原始权重值
            all_weights: 所有权重列表
            
        Returns:
            排名（1-based）
        """
        # 按权重升序排序（越小越靠前）
        sorted_weights = sorted(all_weights)
        
        # 找到当前权重的位置
        try:
            rank = sorted_weights.index(raw_weight) + 1
        except ValueError:
            rank = len(all_weights)
        
        return rank
    
    def calculate_hot_score(self, 
                           raw_weight: float, 
                           all_weights: List[float]) -> Dict[str, Any]:
        """
        计算单条数据的综合热度分
        
        Args:
            raw_weight: 原始权重值
            all_weights: 所有权重列表（用于计算相对排名）
            
        Returns:
            包含排名、排名分数、热度分的字典
        """
        # 1. 计算排名（1为最热）
        rank = self.weight_to_rank(raw_weight, all_weights)
        total = len(all_weights)
        
        # 2. 计算排名分数（基于排名）
        rank_score = self.rank_to_score(rank, total)
        
        # 3. 计算热度分（基于原始权重的归一化）
        # 权重范围：[min_weight, max_weight]，越小越热
        min_weight = min(all_weights)
        max_weight = max(all_weights)
        
        if max_weight > min_weight:
            # 归一化：权重越小，热度分越高
            heat_score = (max_weight - raw_weight) / (max_weight - min_weight) * 100
        else:
            heat_score = 50
        
        # 4. 综合热度分 = 排名分数 × 0.7 + 热度分 × 0.3
        comprehensive_score = rank_score * 0.7 + heat_score * 0.3
        
        return {
            'rank': rank,
            'total_count': total,
            'rank_score': round(rank_score, 2),
            'heat_score': round(heat_score, 2),
            'comprehensive_score': round(comprehensive_score, 2),
            'raw_weight': raw_weight,
            'min_weight': min_weight,
            'max_weight': max_weight
        }
    
    def process_cleaned_data(self, cleaned_items: List[Dict]) -> List[Dict]:
        """
        处理清洗后的数据，添加排名和热度分数
        
        Args:
            cleaned_items: 清洗后的数据列表
            
        Returns:
            添加了排名和热度分数的数据列表
        """
        if not cleaned_items:
            print("[警告] 无数据可处理")
            return []
        
        print(f"[处理] 开始计算排名和热度分数，共 {len(cleaned_items)} 条数据")
        
        # 提取所有权重
        all_weights = [item['raw_weight'] for item in cleaned_items]
        
        # 为每条数据计算排名和分数
        for item in cleaned_items:
            scores = self.calculate_hot_score(item['raw_weight'], all_weights)
            
            # 添加计算结果到原数据
            item['rank_global'] = scores['rank']
            item['rank_score'] = scores['rank_score']
            item['heat_score'] = scores['heat_score']
            item['comprehensive_score'] = scores['comprehensive_score']
        
        # 按综合热度分降序排序（分数越高越热）
        processed_items = sorted(cleaned_items, 
                                 key=lambda x: x['comprehensive_score'], 
                                 reverse=True)
        
        # 更新全局排名
        for idx, item in enumerate(processed_items, 1):
            item['global_rank_final'] = idx
        
        print(f"[处理] 完成排名计算，综合热度分范围: "
              f"{processed_items[-1]['comprehensive_score']:.2f} ~ "
              f"{processed_items[0]['comprehensive_score']:.2f}")
        
        return processed_items
    
    def get_top_n(self, items: List[Dict], n: int = 20) -> List[Dict]:
        """
        获取前N条热点
        
        Args:
            items: 处理后的数据列表
            n: 要获取的数量
            
        Returns:
            前N条热点列表
        """
        return items[:n]
    
    def save_ranking_result(self, items: List[Dict], output_path: str):
        """
        保存排名计算结果
        
        Args:
            items: 处理后的数据列表
            output_path: 输出文件路径
        """
        # 确保目录存在（修复 Windows 路径问题）
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
                print(f"[创建] 创建目录: {output_dir}")
            except Exception as e:
                print(f"[警告] 目录创建失败: {e}")
                # 尝试使用相对路径
                output_path = os.path.basename(output_path)
                output_dir = '.'
        
        # 保存文件
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"[保存] 排名结果已保存至: {output_path}")
        except Exception as e:
            print(f"[错误] 保存失败: {e}")
            # 备选：保存到当前目录
            fallback_path = f"ranking_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(fallback_path, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"[保存] 已保存到备选路径: {fallback_path}")
    
    def print_ranking_report(self, items: List[Dict], top_n: int = 20):
        """
        打印排名报告
        
        Args:
            items: 处理后的数据列表
            top_n: 显示前N条
        """
        print("\n" + "="*70)
        print(f" {self.PROJECT_NAME} - 热度排名报告")
        print("="*70)
        
        print(f"\n【排名说明】")
        print(f"  综合热度分: 0-100分，越高表示热度越高")
        print(f"  排名分数: 基于排名的指数衰减分数")
        print(f"  热度分数: 基于原始权重的归一化分数")
        print(f"  衰减因子: {self.DECAY_FACTOR}")
        
        print(f"\n【TOP {min(top_n, len(items))} 热点排名】")
        print("-" * 70)
        print(f"{'排名':<4} {'综合分':<6} {'权重':<8} {'标题'}")
        print("-" * 70)
        
        for i, item in enumerate(items[:top_n], 1):
            title_display = item['title'][:50] + '...' if len(item['title']) > 50 else item['title']
            print(f"{i:<4} {item['comprehensive_score']:<6.1f} "
                  f"{item['raw_weight']:<8.4f} {title_display}")
        
        # 分数分布统计
        scores = [item['comprehensive_score'] for item in items]
        print(f"\n【分数分布统计】")
        print(f"  最高分: {max(scores):.2f}")
        print(f"  最低分: {min(scores):.2f}")
        print(f"  平均分: {sum(scores)/len(scores):.2f}")
        print(f"  中位数: {sorted(scores)[len(scores)//2]:.2f}")
        
        print("\n" + "="*70)


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
    print(f"[信息] 加载清洗数据: {os.path.basename(latest_file)}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        cleaned_items = json.load(f)
    
    print(f"[信息] 加载 {len(cleaned_items)} 条数据")
    
    # 初始化排名引擎
    engine = RankingEngine()
    
    # 处理排名计算
    ranked_items = engine.process_cleaned_data(cleaned_items)
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d")
    output_path = os.path.join(output_dir, f'ranking_result_{timestamp}.json')
    engine.save_ranking_result(ranked_items, output_path)
    
    # 打印报告
    engine.print_ranking_report(ranked_items, top_n=20)