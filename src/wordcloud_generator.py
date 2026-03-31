#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社交媒体热点词分析项目
词云生成模块（水平显示版，支持类别标识）

优化内容：
1. 所有词水平显示，易于阅读
2. 填满整个画布，无空白区域
3. 显示高频词 Top 30
4. 文件名包含类别标识（general/tech/all），避免混淆
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
    词云生成器（水平显示版，支持类别标识）
    所有词水平显示，填满画布，文件名包含类别信息
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
    
    # ==================== 扩充后的停用词表 ====================
    EXTRA_STOPWORDS = {
        # ========== 基础停用词 ==========
        # 疑问词
        '什么', '怎么', '为什么', '如何', '哪些', '谁', '吗', '呢', '吧',
        '哪里', '何时', '何处', '咋', '干嘛', '为啥', '怎样', '怎么样',
        # 虚词
        '的', '了', '是', '在', '和', '与', '或', '等', '有', '被', '把',
        '就', '都', '也', '还', '要', '会', '能', '可以', '可能', '能够',
        '这', '那', '之', '其', '于', '为', '以', '所', '不', '而', '且',
        # 代词
        '我', '你', '他', '她', '它', '我们', '你们', '他们', '她们', '它们',
        '自己', '别人', '大家', '人家', '本人', '俺', '咱',
        # 连词
        '但是', '然而', '虽然', '因为', '所以', '因此', '于是', '那么',
        '以及', '并且', '而且', '或者', '还是', '要么', '不仅', '不但',
        '尽管', '即使', '如果', '假如', '要是', '无论', '不管',
        # 程度词
        '很', '太', '更', '最', '极', '非常', '特别', '尤其', '比较', '相当',
        '稍微', '略微', '几乎', '大约', '大概', '左右', '上下',
        # 时间词
        '今天', '昨天', '明天', '现在', '过去', '未来', '之前', '之后',
        '以前', '以后', '目前', '当下', '曾经', '已经', '正在', '即将',
        '刚刚', '马上', '立刻', '瞬间',
        # 量词
        '个', '条', '只', '支', '张', '件', '种', '类', '次', '遍', '回', '下',
        '一个', '一种', '一次', '一下', '一点', '一些', '很多', '许多',
        # 无意义词
        '这是', '东西', '这么', '那么', '这样', '那样', '一样', '而已',
        '的话', '来说', '而言', '来讲', '来看', '总之', '实际上',
        '情况', '第一', '时间', '发现', '导致', '要求', '预言', '跑马',
        '处于', '以来', '时期', '年度', '征文', '背后', '原理', '事关',
        '终于', '规来', '承认', '不再',
        
        # ========== 国家方略/政治类 ==========
        '中央', '国家', '政府', '国务院', '中共中央', '总书记', '主席', '总理',
        '党和国家', '全国人大', '全国政协', '国务院总理', '国家主席',
        '中国共产党', '党中央', '国务院常务会议', '国家领导人', '党和国家领导人',
        '国家政策', '国家战略', '国家规划', '国家发展', '国家建设', '国家治理',
        '中国特色社会主义', '中国梦', '中华民族伟大复兴', '新发展理念',
        '高质量发展', '共同富裕', '中国式现代化', '一带一路', '人类命运共同体',
        '脱贫攻坚', '乡村振兴', '生态文明', '绿色发展', '碳达峰', '碳中和',
        '科技创新', '科技强国', '人才强国', '教育强国', '健康中国', '平安中国',
        '法治中国', '数字中国', '美丽中国', '网络强国', '制造强国', '质量强国',
        '航天强国', '交通强国', '海洋强国', '文化强国', '体育强国', '农业强国',
        '依法治国', '从严治党', '改革开放', '经济特区', '自贸区', '自贸港',
        
        # ========== 时政/军事类 ==========
        '外交部', '国防部', '解放军', '军队', '军事', '演习', '军演', '国防',
        '武器装备', '导弹', '航母', '战机', '军舰', '潜艇', '核武器',
        '战略', '战术', '军事行动', '军事演习', '军事训练', '军事合作',
        '军事交流', '军事援助', '军事基地', '军事部署', '边防', '海防',
        
        # ========== 经济/金融类 ==========
        '央行', '财政部', '发改委', '证监会', '银保监会', '金融监管',
        '货币政策', '财政政策', '宏观经济', '微观经济', '经济数据',
        '经济指标', 'GDP', 'CPI', 'PPI', 'PMI', '经济增速', '经济增长',
        '经济复苏', '经济下行', '经济压力', '经济形势', '经济分析',
        '统计局', '人民银行', '商业银行', '金融机构', '资本市场',
        '股市', '债市', '汇市', '期货', '期权', '基金', '保险',
        
        # ========== 社会/民生类 ==========
        '民生', '就业', '教育', '医疗', '社保', '养老', '住房', '交通',
        '环境', '环保', '生态', '资源', '能源', '粮食', '食品安全',
        '公共卫生', '疫情防控', '疫苗接种', '核酸检测', '隔离', '封控',
        '社区', '街道', '居委会', '村委会', '志愿者', '公益', '慈善',
        
        # ========== 疾病/健康类 ==========
        '癌症', '肿瘤', '白血病', '艾滋病', '糖尿病', '高血压', '心脏病',
        '抑郁症', '焦虑症', '自闭症', '老年痴呆', '帕金森', '阿尔茨海默',
        '流感', '肺炎', '新冠', '疫情', '病毒', '感染', '疫苗', '药物',
        '治疗', '手术', '康复', '痊愈', '治愈', '诊断', '检查', '体检',
        '医院', '医生', '护士', '患者', '病人', '病房', '门诊', '急诊',
        
        # ========== 仿真/技术类 ==========
        '仿真', '模拟', '建模', '算法', '模型', '参数', '系统', '框架',
        '架构', '架构设计', '系统架构', '软件架构', '技术架构',
        '平台架构', '技术方案', '技术路线', '技术规划', '技术平台',
        '数据', '数据库', '数据挖掘', '数据分析', '大数据', '云计算',
        '人工智能', 'AI', '机器学习', '深度学习', '神经网络', '大模型',
        '区块链', '元宇宙', '物联网', '5G', '6G', '芯片', '半导体',
        
        # ========== 教育/学术类 ==========
        '教育', '学校', '大学', '学院', '中学', '小学', '幼儿园',
        '学生', '老师', '教授', '博士', '硕士', '本科', '研究生',
        '课程', '专业', '学科', '科研', '研究', '论文', '学术',
        '考试', '高考', '中考', '考研', '留学', '培训', '辅导',
        
        # ========== 科技/互联网类 ==========
        '科技', '技术', '创新', '研发', '专利', '产品', '数码', '智能硬件',
        '互联网', '移动互联网', 'APP', '应用', '软件', '程序', '代码',
        '开源', 'GitHub', 'Git', '编程', '开发', '前端', '后端', '全栈',
        'React', 'Vue', 'Angular', 'Python', 'Java', 'JavaScript',
        'C++', 'Go', 'Rust', 'Swift', 'Kotlin', 'Flutter', 'Docker',
        
        # ========== 娱乐/文化类 ==========
        '电影', '电视剧', '综艺', '节目', '明星', '艺人', '偶像', '粉丝',
        '音乐', '歌曲', '专辑', '演唱会', '舞台', '表演', '演技', '导演',
        '编剧', '票房', '收视率', '评分', '口碑', '热搜', '话题',
        
        # ========== 体育/竞技类 ==========
        '体育', '运动', '比赛', '赛事', '冠军', '亚军', '季军', '金牌',
        '银牌', '铜牌', '运动员', '教练', '裁判', '球队', '俱乐部',
        '足球', '篮球', '网球', '乒乓球', '羽毛球', '游泳', '田径',
        '奥运会', '世界杯', '欧冠', 'NBA', 'CBA', '中超', '英超',
        
        # ========== 其他 ==========
        '表示', '指出', '强调', '认为', '称', '说', '谈', '讲', '聊',
        '报道', '消息', '据悉', '据了解', '相关人士', '知情人士',
        '透露', '披露', '曝光', '爆料', '泄露', '公开', '公布', '发布',
        '宣布', '通告', '公告', '声明', '回应', '回复', '答复',
        '召开', '举行', '举办', '开展', '启动', '开幕', '闭幕',
        '会议', '论坛', '峰会', '座谈会', '研讨会', '发布会'
        '看到', '一杯', '群众', '最近', '一天', '再见', '为何',
        '少数派', '编辑', '玩意', '出来', '看待', '进入', '本周',
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

        # ── Linux 字体路径（Docker 容器，优先检查）──
        # apt-get install fonts-wqy-microhei 安装后的标准路径
        linux_font_paths = [
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',  # Debian/Ubuntu 标准路径
            '/usr/share/fonts/wqy-microhei/wqy-microhei.ttc',  # 部分发行版备选路径
        ]

        # ── Windows 字体路径（本地开发环境，次优先）──
        windows_font_paths = [
            'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
            'C:/Windows/Fonts/simhei.ttf',  # 黑体
            'C:/Windows/Fonts/simsun.ttc',  # 宋体
            'C:/Windows/Fonts/simkai.ttf',  # 楷体
        ]

        # 合并路径列表，Linux 优先
        font_paths = linux_font_paths + windows_font_paths

        for path in font_paths:
            if os.path.exists(path):
                self.config['font_path'] = path
                font_name = os.path.basename(path)
                print(f"[字体] 使用字体: {font_name} ({path})")
                return

        print("[字体] 未找到中文字体，将使用默认字体（中文可能显示为方块）")
    
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
                                   output_dir: str = None,
                                   category: str = 'all') -> Dict[str, Any]:
        """
        从清洗数据生成词云
        
        Args:
            cleaned_items: 清洗后的数据列表
            output_dir: 输出目录
            category: 类别标识 'general', 'tech', 'all'
            
        Returns:
            词云结果字典，包含文件路径
        """
        print(f"[处理] 开始生成词云，共 {len(cleaned_items)} 条热点数据")
        
        # 获取高频词 Top 30
        top_n = self.config['max_words']
        word_freq = self.get_top_words(cleaned_items, top_n)
        
        # 打印高频词列表
        print(f"\n{'='*70}")
        print(f"【词云高频词 Top {len(word_freq)}】（{category} - 全部水平显示）")
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
        
        # 生成带类别标识的输出路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f'wordcloud_{category}_{timestamp}.png')
        freq_output = os.path.join(output_dir, f'word_freq_{category}_{timestamp}.json')
        
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
            'output_path': output_path,
            'category': category
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
    
    # 生成词云（使用默认类别 'all'）
    result = generator.generate_from_cleaned_data(cleaned_items, output_dir, category='all')
    
    print(f"\n{'='*70}")
    print(f"[完成] 词云生成完成")
    print(f"  总词数: {result['total_words']}")
    print(f"  Top 10: {[w for w, _ in result['top_words'][:10]]}")
    print(f"  图片路径: {result['output_path']}")
    print(f"{'='*70}")