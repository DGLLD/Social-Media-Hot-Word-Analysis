#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据清洗模块测试
"""

import os
import sys
import json

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_cleaner import DataCleaner


def test_parse_file():
    """测试文件解析功能"""
    cleaner = DataCleaner()
    
    # 模拟文件内容
    mock_content = """0.0200
嘴唇发紫 心脏不好
https://s.weibo.com/...
0.0400
白日提灯OST官宣
https://s.weibo.com/..."""
    
    # 写入临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
        f.write(mock_content)
        temp_path = f.name
    
    try:
        items = cleaner.parse_file(temp_path)
        print(f"解析结果: {len(items)} 条")
        for item in items:
            print(f"  - 权重: {item['raw_weight']}, 标题: {item['title'][:30]}...")
    finally:
        os.unlink(temp_path)


def test_tokenize():
    """测试分词功能"""
    cleaner = DataCleaner()
    
    test_titles = [
        "嘴唇发紫 心脏不好",
        "这就是中国AI产业链的硬核实力",
        "张雪峰因心源性猝死抢救无效去世"
    ]
    
    print("\n分词测试:")
    for title in test_titles:
        words, count = cleaner.tokenize_title(title)
        print(f"标题: {title}")
        print(f"分词: {words}")
        print(f"词数: {count}\n")


def test_full_clean():
    """测试完整清洗流程"""
    cleaner = DataCleaner()
    
    # 使用实际的测试文件（如果存在）
    project_root = os.path.dirname(os.path.dirname(__file__))
    raw_dir = os.path.join(project_root, 'data', 'raw')
    
    if os.path.exists(raw_dir):
        file_paths = [os.path.join(raw_dir, f) for f in os.listdir(raw_dir) if f.endswith('.txt')]
        if file_paths:
            items = cleaner.clean_multiple_files(file_paths)
            print(f"\n清洗完成: {len(items)} 条数据")
            
            # 打印前3条
            print("\n前3条数据:")
            for i, item in enumerate(items[:3]):
                print(f"\n{i+1}. ID: {item['id']}")
                print(f"   标题: {item['title']}")
                print(f"   权重: {item['raw_weight']} (越小越热)")
                print(f"   全局排名: {item['global_rank']}")
                print(f"   分词: {item['words'][:8]}...")
    else:
        print("未找到测试数据文件")


if __name__ == '__main__':
    print("="*50)
    print("数据清洗模块测试")
    print("="*50)
    
    test_parse_file()
    test_tokenize()
    test_full_clean()