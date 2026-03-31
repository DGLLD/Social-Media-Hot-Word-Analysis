-- =============================================
-- 社交媒体热点词分析项目 - 数据库初始化脚本
-- 创建时间: 2026-03-27
-- =============================================

-- ========== 综合类热榜表 ==========
CREATE TABLE IF NOT EXISTS hot_rank_common (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    normalized_score REAL NOT NULL DEFAULT 0,
    title TEXT NOT NULL,
    url TEXT,
    crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引：按爬取时间查询
CREATE INDEX IF NOT EXISTS idx_crawl_time_common ON hot_rank_common(crawl_time);

-- 创建索引：按标题搜索
CREATE INDEX IF NOT EXISTS idx_title_common ON hot_rank_common(title);


-- ========== 科技类热榜表 ==========
CREATE TABLE IF NOT EXISTS hot_rank_tech (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    normalized_score REAL NOT NULL DEFAULT 0,
    title TEXT NOT NULL,
    url TEXT,
    crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引：按爬取时间查询
CREATE INDEX IF NOT EXISTS idx_crawl_time_tech ON hot_rank_tech(crawl_time);

-- 创建索引：按标题搜索
CREATE INDEX IF NOT EXISTS idx_title_tech ON hot_rank_tech(title);


-- ========== 查看表信息 ==========
-- 查询表结构
SELECT '表 hot_rank_common 创建成功' AS message;
SELECT '表 hot_rank_tech 创建成功' AS message;