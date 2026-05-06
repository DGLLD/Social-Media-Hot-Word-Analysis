# 社交媒体热点词分析平台

> 一个基于 Flask + SnowNLP + 千问大模型的全栈热点词分析系统，实现多平台热搜采集、情感分析、词云可视化与 AI 深度解读。

---

## 📌 项目简介

本项目是一个**全栈式社交媒体热点词分析平台**，能够自动采集微博、知乎、百度、微信、贴吧、36氪、少数派、虎嗅、IT之家、掘金等 10 个平台的热搜榜单，通过自然语言处理技术进行情感分析，并利用千问大模型生成热点深度解读，帮助用户快速了解社交媒体热点及其舆论情感倾向。

---

## 🎯 核心功能

| 功能模块 | 说明 |
|----------|------|
| 🔥 **多平台热榜采集** | 并行爬取 10 个平台热搜，自动归一化权重 |
| 🧹 **数据清洗与分词** | jieba 中文分词 + 204 个停用词过滤 |
| 📊 **热度排名加权** | 指数衰减公式 + 加权融合，计算综合热度分 |
| 😊 **情感分析** | 分级词典 + 规则引擎 + SnowNLP，准确率 87.8% |
| ☁️ **词云生成** | 高频词统计 + wordcloud，支持综合/科技双榜 |
| 🤖 **AI 深度解读** | 千问大模型接入，自动生成热点事件分析报告 |
| 🔄 **一键刷新** | 支持强制更新数据，实时获取最新热点 |
| 📱 **响应式设计** | 支持 PC 端和移动端访问 |

---

## 🛠️ 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 后端框架 | Flask | 3.0.0 |
| 数据库 | SQLite | 内置 |
| 爬虫 | requests + lxml | 2.31.0 + 4.9.3 |
| 中文分词 | jieba | 0.42.1 |
| 情感分析 | SnowNLP | 0.12.3 |
| 词云生成 | wordcloud + matplotlib | 1.9.3 + 3.8.0 |
| 大模型 | 千问 API（qwen-plus） | - |
| 前端 | HTML5/CSS3/JavaScript + ECharts + SweetAlert2 | - |

---

## 📁 项目结构

```
社交媒体热点词分析项目/
├── config/                      # 配置文件
│   ├── stopwords.txt            # 停用词表（204个）
│   ├── category_keywords.json   # 分类关键词库
│   └── llm_config.json          # 大模型配置（API密钥）
├── data/
│   ├── raw/                     # 原始爬虫数据
│   └── processed/               # 清洗后数据
├── database/                    # 数据库目录
│   ├── schema.sql               # 建表脚本
│   └── hotspot.db               # SQLite 数据库
├── output/                      # 输出目录
│   ├── rankings/                # 排名结果 JSON
│   ├── wordclouds/              # 词云图片 PNG
│   └── sentiment/               # 情感分析结果 JSON
├── src/                         # 源代码
│   ├── templates/
│   │   └── service.html         # 前端页面
│   ├── app.py                   # Flask 后端服务
│   ├── crawler.py               # 爬虫模块
│   ├── data_cleaner.py          # 数据清洗模块
│   ├── ranking_engine.py        # 排名加权计算
│   ├── ranking_processor.py     # 排行处理
│   ├── wordcloud_generator.py   # 词云生成
│   ├── sentiment_analyzer.py    # 情感分析
│   ├── llm_enhancer.py          # 大模型增强
│   └── db_connect.py            # 数据库连接
├── static/                      # 静态文件
│   └── service2.png             # 背景图
├── tools/                       # 工具脚本
├── requirements.txt             # 依赖列表
└── README.md                    # 项目说明
```

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.12+
- pip 包管理器

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 初始化数据库

```bash
python src/crawler.py
```

### 4. 启动服务

```bash
python src/app.py
```

### 5. 访问页面

打开浏览器访问：**http://127.0.0.1:5000**

---

## 🔧 核心算法

### 排名加权公式

```
rank_score = 100 × 0.85^(rank-1)
heat_score = (max_weight - raw_weight) / (max_weight - min_weight) × 100
comprehensive_score = rank_score × 0.7 + heat_score × 0.3
```

### 情感分析公式

```
lexicon_score = pos_count / (pos_count + neg_count)
final_score = snow_score × 0.3 + lexicon_score × 0.7
```

### 情感词典分级

| 级别 | 正面词示例 | 负面词示例 | 权重 |
|------|------------|------------|------|
| 强 | 夺冠、金牌、里程碑 | 去世、猝死、崩盘 | 3 |
| 中 | 突破、大涨、创新 | 暴跌、危机、争议 | 2 |
| 弱 | 教程、攻略、推荐 | 示弱、妥协、曝光 | 1 |

---

## 📊 数据流

```
爬虫采集 → 数据清洗 → 排名计算 → 情感分析 → 词云生成 → Flask API → 前端展示
```

---

## 📈 性能指标

| 指标 | 数值 |
|------|------|
| 情感分析准确率 | 87.8% |
| API 响应时间 | 45-120ms |
| 爬虫采集耗时 | 约 8 秒（10 个平台并行） |
| 单条情感分析 | < 5ms |

---

## 🔌 API 接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/general_ranking` | GET | 综合热榜排行 |
| `/api/tech_ranking` | GET | 科技热榜排行 |
| `/api/general_wordcloud` | GET | 综合词云图片 |
| `/api/tech_wordcloud` | GET | 科技词云图片 |
| `/api/general_sentiment` | GET | 综合情感统计 |
| `/api/tech_sentiment` | GET | 科技情感统计 |
| `/api/hotword_detail/{rank}` | GET | 热点详情 |
| `/api/analyze` | POST | AI 深度解读 |
| `/api/search_news` | GET | 新闻搜索 |
| `/api/refresh` | POST | 强制刷新数据 |

---

## 📝 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | 千问大模型 API 密钥 | 空（可在前端配置） |

---

## 🧪 运行测试

```bash
# 单元测试
python -m unittest discover tests

# 情感分析测试
python src/sentiment_analyzer.py

# 爬虫测试（强制模式）
python src/crawler.py --force
```
---

## 🤝 团队分工

| 成员 | 职责 |
|------|------|
| 周艺侬 | 数据处理模块、模型训练模块、情感分析、词云生成 |
| 姚宇轩 | Flask 后端服务、爬虫开发、移动端适配 |
| 黄然 | 后端服务封装、报告导出、页面适配 |

---

## 📄 开源协议

本项目仅供学习交流使用。

---

## 🙏 致谢

- [SnowNLP](https://github.com/isnowfy/snownlp) - 中文情感分析库
- [jieba](https://github.com/fxsjy/jieba) - 中文分词库
- [wordcloud](https://github.com/amueller/word_cloud) - 词云生成库
- [Flask](https://flask.palletsprojects.com/) - 轻量级 Web 框架
- [阿里云百炼](https://bailian.console.aliyun.com/) - 千问大模型 API

---

## 📧 联系方式

如有问题，请联系项目维护者。

---

**⭐ 如果觉得这个项目对你有帮助，欢迎给个 Star！**
