# GitHub新闻项目

一个基于Flask的GitHub项目新闻聚合平台，专注于AI领域的热门项目展示和数据分析。

## 项目特色

- 🚀 实时同步GitHub热门AI项目
- 🔍 支持多维度搜索和筛选
- 📊 智能排序（星标、更新时间、名称）
- ⏰ 定时自动更新数据
- 📈 详细的统计分析
- 📱 响应式设计，移动端友好

## 技术栈

- **后端：** Python Flask
- **数据库：** MySQL 8
- **前端：** Bootstrap 5 + Font Awesome
- **API：** GitHub REST API
- **定时任务：** APScheduler
- **ORM：** SQLAlchemy

## 项目结构

```
githubnews/
├── app/
│   ├── __init__.py          # Flask应用工厂
│   ├── models.py            # 数据库模型
│   ├── routes.py            # 主要路由
│   ├── api.py               # API路由
│   ├── services.py          # 业务逻辑服务
│   ├── scheduler.py         # 定时任务
│   └── templates/           # HTML模板
│       ├── base.html        # 基础模板
│       ├── index.html       # 首页
│       ├── stats.html       # 统计页面
│       └── about.html       # 关于页面
├── database/
│   └── create_tables.sql    # 数据库建表脚本
├── config.py                # 配置文件
├── app.py                   # 应用入口
├── requirements.txt         # 依赖包
└── README.md               # 项目说明
```

## 安装和运行

### 1. 环境要求

- Python 3.8+
- MySQL 8.0+

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 数据库配置

1. 创建MySQL数据库：
```sql
CREATE DATABASE github_news CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. 执行建表脚本：
```bash
mysql -u root -p github_news < database/create_tables.sql
```

3. 修改配置文件 `config.py` 中的数据库连接信息：
```python
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'zhang'  # 修改为你的密码
MYSQL_DATABASE = 'github_news'
```

### 4. GitHub API配置（可选）

为了提高API请求限制，建议配置GitHub Token：

1. 在GitHub创建Personal Access Token
2. 设置环境变量：
```bash
export GITHUB_TOKEN=your_github_token_here
```

### 5. 启动应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

## 功能说明

### 首页功能

- **项目列表展示：** 项目名称、作者、星标数、Languages、项目地址、更新时间、简介
- **搜索功能：** 
  - 关键字搜索（项目名称和描述）
  - 作者查询
  - 编程语言筛选
- **排序功能：**
  - 按星标数排序
  - 按更新时间排序
  - 按项目名称排序
  - 支持升序/降序

### 数据更新机制

1. **定时刷新：** 每6小时自动执行一次，搜索关键字"AI"，按星标数倒序获取最多1000个项目
2. **手动刷新：** 用户可随时点击刷新按钮，立即获取最新数据
3. **智能去重：** 根据项目名称+作者组合判断唯一性，存在则更新，不存在则新增

### 统计功能

- 项目总数、星标总数、分叉总数统计
- 编程语言分布统计
- 刷新日志记录
- API调用统计

## API接口

系统提供RESTful API接口：

- `GET /api/projects` - 获取项目列表
- `GET /api/projects/{id}` - 获取项目详情
- `POST /api/refresh` - 手动刷新数据
- `GET /api/stats` - 获取统计信息
- `GET /api/languages` - 获取编程语言列表

## 配置说明

主要配置项（`config.py`）：

```python
# 定时任务配置
REFRESH_INTERVAL_HOURS = 6  # 定时刷新间隔(小时)
DEFAULT_SEARCH_KEYWORD = 'AI'  # 默认搜索关键词
MAX_RESULTS_PER_REQUEST = 1000  # 每次请求最大结果数

# 分页配置
PROJECTS_PER_PAGE = 20  # 每页显示项目数
```

## 数据库表说明

### github_projects（主表）
- 存储GitHub项目的详细信息
- 唯一约束：项目名称+作者
- 包含本地管理字段（抓取次数、更新时间等）

### refresh_logs（刷新日志）
- 记录每次数据刷新的详细信息
- 支持手动/定时刷新类型区分

### system_config（系统配置）
- 存储系统配置参数
- 支持运行时动态修改

### api_stats（API统计）
- 记录API调用统计数据
- 用于监控和分析

## 注意事项

1. **GitHub API限制：**
   - 未认证用户：每小时60次请求
   - 认证用户：每小时5000次请求
   - 建议配置GitHub Token以获得更高限制

2. **数据库性能：**
   - 已添加必要的索引优化查询性能
   - 支持全文搜索索引

3. **定时任务：**
   - 使用APScheduler实现定时任务
   - 任务失败会记录错误日志
   - 支持启动时执行一次初始化刷新

## 开发说明

### 添加新功能
1. 在 `models.py` 中定义数据模型
2. 在 `services.py` 中实现业务逻辑
3. 在 `routes.py` 或 `api.py` 中添加路由
4. 在 `templates/` 中创建或修改模板

### 部署建议
1. 使用Gunicorn作为WSGI服务器
2. 配置Nginx反向代理
3. 设置定时任务守护进程
4. 配置日志轮转

## 许可证

MIT License

## 作者

Flask开发团队 