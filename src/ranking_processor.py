#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
排行处理器模块（优化版 - 分别处理 + 增强科技识别）

功能：
1. 综合热点词排行：使用综合热榜数据
2. 科技热点词排行：使用科技热榜数据
3. 优化科技类关键词识别
4. 分别为综合排行和科技排行生成词云
"""

import os
import json
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ranking_engine import RankingEngine
from src.wordcloud_generator import WordCloudGenerator


class RankingProcessor:
    """
    排行处理器（优化版）
    分别处理综合热榜和科技热榜数据
    """
    
    PROJECT_NAME = "社交媒体热点词分析项目"
    
    # 扩展科技关键词库（用于识别科技类热点）
    TECH_KEYWORDS = {
        # AI/大模型相关
        'AI', '人工智能', '大模型', 'OpenClaw', 'Claude', 'Meta', 'GPT', 'Token', '词元',
        'Sora', 'OpenAI', 'DeepSeek', 'Claude Code', 'LLM', '机器学习', '深度学习',
        '生成式AI', 'AIGC', '智能体', 'Agent',
        # 硬件/手机/电脑
        '鸿蒙', '华为', '小米', '苹果', '腾讯', '阿里', '字节', '芯片', '机器人',
        '手机', 'iPhone', 'Mac', '笔记本', '电脑', '显示器', '平板', '折叠屏',
        '一加', 'OPPO', 'vivo', '荣耀', '三星', '联想',
        # 软件/编程
        '算法', '数据', '智能', '云计算', '5G', '6G', 'WebAssembly', 'React', 'Vue',
        '前端', '后端', '编程', '代码', '开源', '框架', 'API', 'SDK', 'GitHub',
        'Cursor', 'Copilot', 'VS Code', 'Python', 'Java', 'JavaScript',
        # 互联网/科技公司
        '美团', '京东', '百度', '知乎', '微博', '抖音', '微信', '拼多多',
        'B站', '小红书', '快手', '网易', '搜狐', '新浪',
        # 科技事件/产品
        '评测', '发布', '首发', '体验', '更新', '上线', '关停', '开源',
        '预售', '开售', '上市', '曝光', '泄露', '爆料',
        # 其他科技相关
        '科技', '技术', '创新', '研发', '专利', '产品', '数码', '智能硬件',
        '物联网', '车联网', '自动驾驶', '新能源', '电动车', '智能汽车'
    }
    
    def __init__(self, cleaned_data_path: str = None):
        """
        初始化排行处理器
        
        Args:
            cleaned_data_path: 清洗后的数据文件路径
        """
        self.cleaned_data_path = cleaned_data_path
        self.general_items = []  # 综合热榜数据
        self.tech_items = []     # 科技热榜数据
        
        # 初始化子模块
        self.ranking_engine = RankingEngine()
        self.wordcloud_generator = WordCloudGenerator()
        
        print(f"[初始化] {self.PROJECT_NAME} - 排行处理器（分别处理版）")
    
    def _ensure_directory(self, dir_path: str) -> bool:
        """
        确保目录存在，如果路径是文件则删除并创建目录
        """
        try:
            if os.path.exists(dir_path) and not os.path.isdir(dir_path):
                os.remove(dir_path)
                print(f"[修复] 删除文件: {dir_path}，重新创建目录")
            
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                print(f"[创建] 创建目录: {dir_path}")
            return True
        except Exception as e:
            print(f"[警告] 目录处理失败: {e}")
            return False
    
    def load_and_separate_data(self, data_path: str = None) -> tuple:
        """
        加载清洗后的数据，并根据来源文件分离
        
        规则：
        - 文件名包含"综合热榜" -> 综合数据
        - 文件名包含"科技热榜" -> 科技数据
        - 如果没有来源信息，则通过关键词判断
        
        Args:
            data_path: 数据文件路径
            
        Returns:
            (general_items, tech_items)
        """
        path = data_path or self.cleaned_data_path
        if not path:
            raise ValueError("未指定数据文件路径")
        
        with open(path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        print(f"[加载] 读取 {len(items)} 条数据: {os.path.basename(path)}")
        
        general_items = []
        tech_items = []
        unknown_items = []
        
        for item in items:
            # 方法1：根据来源文件判断（如果清洗时保存了source_file）
            source_file = item.get('source_file', '')
            
            if '综合热榜' in source_file or '综合' in source_file:
                general_items.append(item)
            elif '科技热榜' in source_file or '科技' in source_file:
                tech_items.append(item)
            else:
                # 方法2：根据标题内容判断
                title = item.get('title', '')
                if self._is_tech_title(title):
                    tech_items.append(item)
                else:
                    general_items.append(item)
        
        print(f"[分离] 综合热榜数据: {len(general_items)} 条")
        print(f"[分离] 科技热榜数据: {len(tech_items)} 条")
        
        return general_items, tech_items
    
    def _is_tech_title(self, title: str) -> bool:
        """
        判断标题是否属于科技类
        """
        for keyword in self.TECH_KEYWORDS:
            if keyword in title:
                return True
        return False
    
    def process_rankings(self, items: List[Dict], name: str) -> List[Dict]:
        """
        处理排名计算
        
        Args:
            items: 数据列表
            name: 名称（用于日志）
            
        Returns:
            排名后的数据列表
        """
        if not items:
            print(f"[跳过] {name}数据为空，跳过排名计算")
            return []
        
        print(f"\n[处理] 计算{name}排名...")
        ranked_items = self.ranking_engine.process_cleaned_data(items)
        
        return ranked_items
    
    def generate_wordcloud_for_items(self, items: List[Dict], 
                                     output_dir: str,
                                     name: str) -> Dict:
        """
        为指定数据生成词云
        """
        if not items:
            print(f"[跳过] {name}数据为空，跳过词云生成")
            return {}
        
        print(f"\n[处理] 生成{name}词云...")
        
        # 确保输出目录存在
        self._ensure_directory(output_dir)
        
        # 使用 wordcloud_generator 生成词云
        result = self.wordcloud_generator.generate_from_cleaned_data(items, output_dir)
        
        # 重命名输出文件
        if result.get('output_path'):
            old_path = result['output_path']
            dir_name = os.path.dirname(old_path)
            ext = os.path.splitext(old_path)[1]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_path = os.path.join(dir_name, f'wordcloud_{name}_{timestamp}{ext}')
            
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
        """
        if not items:
            print(f"[跳过] {name}数据为空，跳过保存")
            return
        
        self._ensure_directory(output_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f'ranking_{name}_{timestamp}.json')
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"[保存] {name}排名已保存: {os.path.basename(output_path)}")
        except Exception as e:
            print(f"[错误] 保存失败: {e}")
            fallback_path = f'ranking_{name}_{timestamp}.json'
            with open(fallback_path, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"[备选] 已保存到: {fallback_path}")
    
    def print_ranking_report(self, items: List[Dict], name: str, top_n: int = 15):
        """
        打印排行报告
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
        
        scores = [item.get('comprehensive_score', 0) for item in items]
        if scores:
            print("-" * 70)
            print(f"统计: 最高 {max(scores):.1f} | 最低 {min(scores):.1f} | "
                  f"平均 {sum(scores)/len(scores):.1f} | 共{len(items)}条")
    
    def run(self, data_path: str = None, output_dir: str = None):
        """
        执行完整处理流程
        """
        print(f"\n{'='*70}")
        print(f" {self.PROJECT_NAME} - 排行处理（分别处理版）")
        print(f"{'='*70}")
        
        # 1. 加载并分离数据
        general_items, tech_items = self.load_and_separate_data(data_path)
        
        # 2. 设置输出目录
        if output_dir is None:
            project_root = os.path.dirname(os.path.dirname(__file__))
            output_dir = os.path.join(project_root, 'output', 'rankings')
        
        # 3. 确保输出目录存在
        self._ensure_directory(output_dir)
        
        # 4. 确保词云输出目录存在
        wordcloud_output_dir = os.path.join(os.path.dirname(output_dir), 'wordclouds')
        self._ensure_directory(wordcloud_output_dir)
        
        # 5. 处理综合热榜排行
        print(f"\n{'─'*70}")
        print("【综合热榜排行】")
        print(f"{'─'*70}")
        
        general_ranked = self.process_rankings(general_items, "综合热榜")
        self.save_ranking_result(general_ranked, output_dir, "general")
        self.print_ranking_report(general_ranked, "综合热榜", top_n=15)
        
        # 6. 生成综合热榜词云
        general_wordcloud = self.generate_wordcloud_for_items(
            general_ranked, wordcloud_output_dir, "general"
        )
        
        # 7. 处理科技热榜排行
        print(f"\n{'─'*70}")
        print("【科技热榜排行】")
        print(f"{'─'*70}")
        
        tech_ranked = self.process_rankings(tech_items, "科技热榜")
        self.save_ranking_result(tech_ranked, output_dir, "tech")
        self.print_ranking_report(tech_ranked, "科技热榜", top_n=15)
        
        # 8. 生成科技热榜词云
        tech_wordcloud = self.generate_wordcloud_for_items(
            tech_ranked, wordcloud_output_dir, "tech"
        )
        
        print(f"\n{'='*70}")
        print("[完成] 排行处理完成")
        print(f"  综合热榜: {len(general_ranked)} 条数据")
        print(f"  科技热榜: {len(tech_ranked)} 条数据")
        print(f"{'='*70}")


# ==================== 主程序入口 ====================
if __name__ == '__main__':
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # 文件路径
    processed_dir = os.path.join(project_root, 'data', 'processed')
    output_dir = os.path.join(project_root, 'output', 'rankings')
    wordcloud_dir = os.path.join(project_root, 'output', 'wordclouds')
    
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
    
    # 预处理：确保输出目录存在
    def ensure_path_is_directory(path):
        if os.path.exists(path) and not os.path.isdir(path):
            try:
                os.remove(path)
                print(f"[修复] 删除文件: {path}")
            except Exception as e:
                print(f"[警告] 无法删除文件: {e}")
    
    ensure_path_is_directory(output_dir)
    ensure_path_is_directory(wordcloud_dir)
    
    # 创建目录
    try:
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(wordcloud_dir, exist_ok=True)
    except Exception as e:
        print(f"[警告] 目录创建失败: {e}")
    
    # 初始化处理器并运行
    processor = RankingProcessor()
    processor.run(latest_file, output_dir)