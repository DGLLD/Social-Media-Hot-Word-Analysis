## README.md

```markdown
# 社交媒体热点词分析平台

## 项目简介

社交媒体热点词分析平台是一个基于 Flask + SnowNLP 的全栈 Web 应用，用于实时爬取、分析和可视化各大平台的热搜榜单。平台提供热点排行榜、词云图、情感分析和热点详情等功能，帮助用户快速了解社交媒体热点话题及其舆论情感倾向。

### 主要功能

| 功能 | 描述 |
|------|------|
| **热点排行榜** | 综合热榜和科技热榜双榜单，展示最热热点词及热度分 |
| **词云图** | 基于热点标题生成高频关键词云图，直观展示核心话题 |
| **情感分析** | 使用 SnowNLP + 情感词典对每条热点进行情感评分，判断情绪类型 |
| **热点详情** | 点击热词查看完整标题、情感分数、情绪类型和原文链接 |
| **双榜单切换** | 支持综合热榜和科技热榜一键切换，数据独立 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12+, Flask, SnowNLP, jieba |
| 前端 | HTML5, CSS3, JavaScript, ECharts |
| 数据处理 | pandas, numpy, wordcloud |
| 部署 | Docker (可选) |

---

## 项目结构

```
社交媒体热点词分析项目/
├── config/                         # 配置文件
│   ├── stopwords.txt               # 停用词表
│   └── category_keywords.json      # 分类关键词库
├── data/
│   ├── raw/                        # 原始爬虫数据
│   │   ├── 综合热榜_*.txt
│   │   └── 科技热榜_*.txt
│   └── processed/                  # 清洗后数据
│       └── cleaned_data_*.json
├── output/
│   ├── rankings/                   # 排名结果
│   │   ├── ranking_general_*.json
│   │   └── ranking_tech_*.json
│   ├── wordclouds/                 # 词云图片
│   │   ├── wordcloud_general_*.png
│   │   └── wordcloud_tech_*.png
│   └── sentiment/                  # 情感分析结果
│       ├── sentiment_general_*.json
│       └── sentiment_tech_*.json
├── src/
│   ├── app.py                      # Flask 后端服务
│   ├── data_cleaner.py             # 数据清洗模块
│   ├── ranking_engine.py           # 排名加权计算模块
│   ├── ranking_processor.py        # 排行处理（综合+科技分离）
│   ├── wordcloud_generator.py      # 词云生成模块
│   ├── sentiment_analyzer.py       # SnowNLP 情感分析模块
│   ├── title_optimizer.py          # 标题优化模块
│   └── templates/
│       └── service.html            # 前端页面
├── requirements.txt                # Python 依赖
└── README.md                       # 项目说明
```

---

## 环境要求

- Python 3.8+
- pip

---

## 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd 社交媒体热点词分析项目
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 准备数据

将爬虫获取的热搜数据放入 `data/raw/` 目录，文件格式为：

```
0.0200
标题文本
https://链接
0.0400
标题文本
https://链接
...
```

> 说明：每三行为一组（权重分数、标题、链接），权重分数越小表示热度越高。

### 4. 运行数据处理流程

```bash
# 步骤1：数据清洗（保留全部数据）
python src/data_cleaner.py

# 步骤2：排行处理（生成综合热榜和科技热榜）
python src/ranking_processor.py

# 步骤3：情感分析
python src/sentiment_analyzer.py
```

### 5. 启动后端服务

```bash
python src/app.py
```

### 6. 访问页面

打开浏览器访问：**http://127.0.0.1:5000**

---

## VS Code 使用指南

### 1. 打开项目

```bash
code .
```

### 2. 配置 Python 解释器

按 `Ctrl+Shift+P` → 输入 `Python: Select Interpreter` → 选择 Python 3.8+ 解释器

### 3. 安装依赖

在 VS Code 终端中运行：

```bash
pip install -r requirements.txt
```

### 4. 运行项目

- 运行单个模块：右键 `.py` 文件 → `Run Python File in Terminal`
- 调试模式：在 `app.py` 中按 `F5` 启动调试

### 5. 常用命令

| 命令 | 说明 |
|------|------|
| `python src/data_cleaner.py` | 数据清洗 |
| `python src/ranking_processor.py` | 排行处理 |
| `python src/sentiment_analyzer.py` | 情感分析 |
| `python src/app.py` | 启动 Web 服务 |

---

## 数据流程说明

```
原始爬虫数据 (data/raw/*.txt)
        ↓
数据清洗 (data_cleaner.py) → 分词、过滤停用词、记录来源
        ↓
清洗数据 (data/processed/cleaned_data_*.json)
        ↓
排行处理 (ranking_processor.py) → 分离综合/科技、计算热度分
        ↓
排名结果 (output/rankings/ranking_*.json)
        ↓
情感分析 (sentiment_analyzer.py) → SnowNLP + 情感词典
        ↓
情感结果 (output/sentiment/sentiment_*.json) + 词云图
        ↓
前端展示 (Flask + service.html)
```

---

## 后续扩展计划

### 1. 连接数据库

当前数据以 JSON 文件存储，后续可升级为 MySQL/PostgreSQL：

```sql
-- 热点词表
CREATE TABLE hotwords (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(500) NOT NULL,
    platform VARCHAR(50),
    rank INT,
    heat_score FLOAT,
    sentiment_score FLOAT,
    sentiment_label VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 词云词频表
CREATE TABLE wordcloud_freq (
    id INT PRIMARY KEY AUTO_INCREMENT,
    word VARCHAR(100),
    freq INT,
    hotword_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2. 实现自动爬虫

配置定时任务（如 APScheduler）定期爬取热搜数据：

```python
# 在 app.py 中添加
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(func=crawl_hotwords, trigger="interval", minutes=10)
scheduler.start()
```

### 3. 用户刷新功能

前端添加刷新按钮，调用后端接口重新触发爬虫和数据处理：

```javascript
// 前端刷新按钮
async function refreshData() {
    const response = await fetch('/api/refresh', { method: 'POST' });
    if (response.ok) {
        alert('数据刷新中，请稍后查看');
        setTimeout(() => location.reload(), 5000);
    }
}
```

后端接口：

```python
@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    # 触发爬虫和数据处理
    subprocess.Popen(['python', 'src/crawler.py'])
    subprocess.Popen(['python', 'src/ranking_processor.py'])
    subprocess.Popen(['python', 'src/sentiment_analyzer.py'])
    return jsonify({'success': True, 'message': '刷新已启动'})
```

### 4. 实现步骤

1. **数据库集成**：修改 `data_cleaner.py` 和 `ranking_processor.py`，将结果写入数据库
2. **自动爬虫**：创建 `src/crawler.py`，定时爬取各平台热搜
3. **刷新功能**：添加 `/api/refresh` 接口，前端增加刷新按钮
4. **异步处理**：使用 Celery 或后台线程处理耗时任务

---

## 常见问题

### Q1: 运行 `python src/app.py` 时提示模块找不到？

```bash
# 确保在项目根目录下运行
cd 社交媒体热点词分析项目
python src/app.py
```

### Q2: 词云图片显示乱码？

安装中文字体（Windows 已自带），或修改 `wordcloud_generator.py` 中的字体路径。

### Q3: 情感分析结果不准确？

可扩展情感词典，在 `sentiment_analyzer.py` 的 `POSITIVE_WORDS` 和 `NEGATIVE_WORDS` 中添加自定义词汇。

### Q4: 如何添加新的平台数据？

1. 将新平台数据放入 `data/raw/` 目录
2. 在 `ranking_processor.py` 的 `TECH_KEYWORDS` 中添加识别关键词
3. 重新运行数据处理流程

---

## 依赖清单

```
Flask==3.0.0
flask-cors==4.0.0
snownlp==0.12.3
jieba==0.42.1
wordcloud==1.9.3
matplotlib==3.8.0
numpy==1.24.3
```

---

## 联系方式

如有问题，请联系项目维护者。

---

## 版本记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-03-26 | 初始版本，支持综合热榜、科技热榜、词云、情感分析 |
```