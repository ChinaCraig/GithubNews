-- GitHub新闻项目数据库建表脚本
-- 数据库: github_news

-- 创建数据库
CREATE DATABASE IF NOT EXISTS github_news CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE github_news;

-- 创建GitHub项目表
CREATE TABLE IF NOT EXISTS github_projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL COMMENT '项目名称',
    full_name VARCHAR(255) NOT NULL COMMENT '完整项目名称 (owner/repo)',
    owner VARCHAR(255) NOT NULL COMMENT '项目作者',
    description LONGTEXT COMMENT '项目简介',
    html_url VARCHAR(500) NOT NULL COMMENT 'GitHub项目地址',
    stars_count INT DEFAULT 0 COMMENT '星标数量',
    forks_count INT DEFAULT 0 COMMENT '分叉数量',
    watchers_count INT DEFAULT 0 COMMENT '关注者数量',
    language VARCHAR(100) COMMENT '主要编程语言',
    topics JSON COMMENT '项目主题标签',
    license_name VARCHAR(100) COMMENT '许可证名称',
    default_branch VARCHAR(100) DEFAULT 'main' COMMENT '默认分支',
    is_private BOOLEAN DEFAULT FALSE COMMENT '是否私有项目',
    is_fork BOOLEAN DEFAULT FALSE COMMENT '是否为分叉项目',
    created_at DATETIME COMMENT 'GitHub上的创建时间',
    updated_at DATETIME COMMENT 'GitHub上的更新时间',
    pushed_at DATETIME COMMENT '最后推送时间',
    size_kb INT DEFAULT 0 COMMENT '项目大小(KB)',
    open_issues_count INT DEFAULT 0 COMMENT '开放问题数量',
    has_issues BOOLEAN DEFAULT TRUE COMMENT '是否开启Issues',
    has_projects BOOLEAN DEFAULT TRUE COMMENT '是否开启Projects',
    has_wiki BOOLEAN DEFAULT TRUE COMMENT '是否开启Wiki',
    archived BOOLEAN DEFAULT FALSE COMMENT '是否已归档',
    disabled BOOLEAN DEFAULT FALSE COMMENT '是否已禁用',
    visibility VARCHAR(20) DEFAULT 'public' COMMENT '可见性',
    
    -- 本地管理字段
    local_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '本地创建时间',
    local_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '本地更新时间',
    last_fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '最后抓取时间',
    fetch_count INT DEFAULT 1 COMMENT '抓取次数',
    
    -- 索引
    UNIQUE KEY unique_project (name, owner),
    INDEX idx_full_name (full_name),
    INDEX idx_owner (owner),
    INDEX idx_stars (stars_count DESC),
    INDEX idx_language (language),
    INDEX idx_updated_at (updated_at DESC),
    INDEX idx_created_at (created_at DESC),
    INDEX idx_local_updated (local_updated_at DESC),
    
    -- 全文搜索索引
    FULLTEXT KEY ft_search (name, owner, description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='GitHub项目信息表';

-- 创建刷新日志表
CREATE TABLE IF NOT EXISTS refresh_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    refresh_type ENUM('manual', 'scheduled') NOT NULL COMMENT '刷新类型',
    keyword VARCHAR(255) NOT NULL COMMENT '搜索关键词',
    total_fetched INT DEFAULT 0 COMMENT '获取的项目总数',
    new_projects INT DEFAULT 0 COMMENT '新增项目数',
    updated_projects INT DEFAULT 0 COMMENT '更新项目数',
    start_time TIMESTAMP NOT NULL COMMENT '开始时间',
    end_time TIMESTAMP NULL COMMENT '结束时间',
    duration_seconds INT DEFAULT 0 COMMENT '耗时(秒)',
    status ENUM('running', 'success', 'failed') DEFAULT 'running' COMMENT '状态',
    error_message TEXT COMMENT '错误信息',
    api_requests_count INT DEFAULT 0 COMMENT 'API请求次数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_refresh_type (refresh_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='刷新日志表';

-- 创建系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description VARCHAR(255) COMMENT '配置描述',
    config_type ENUM('string', 'int', 'float', 'boolean', 'json') DEFAULT 'string' COMMENT '配置类型',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- 插入默认配置
INSERT INTO system_config (config_key, config_value, description, config_type) VALUES
('refresh_interval_hours', '6', '定时刷新间隔(小时)', 'int'),
('default_search_keyword', 'AI', '默认搜索关键词', 'string'),
('max_results_per_request', '1000', '每次请求最大结果数', 'int'),
('projects_per_page', '20', '每页显示项目数', 'int'),
('enable_scheduled_refresh', 'true', '是否启用定时刷新', 'boolean'),
('github_api_token', '', 'GitHub API Token (可选)', 'string');

-- 创建API请求统计表
CREATE TABLE IF NOT EXISTS api_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL COMMENT '日期',
    total_requests INT DEFAULT 0 COMMENT '总请求数',
    successful_requests INT DEFAULT 0 COMMENT '成功请求数',
    failed_requests INT DEFAULT 0 COMMENT '失败请求数',
    rate_limit_hits INT DEFAULT 0 COMMENT '触发限制次数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_date (date),
    INDEX idx_date (date DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API请求统计表'; 