import os
from datetime import timedelta

class Config:
    # 应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'github-news-secret-key-2024'
    
    # 数据库配置
    MYSQL_HOST = 'localhost'
    MYSQL_PORT = 3306
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'zhang'
    MYSQL_DATABASE = 'github_news'
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'echo': False
    }
    
    # GitHub API配置
    GITHUB_API_BASE_URL = 'https://api.github.com'
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')  # 可选，用于提高API限制
    
    # 定时任务配置
    REFRESH_INTERVAL_HOURS = 6  # 每6小时刷新一次
    DEFAULT_SEARCH_KEYWORD = 'AI'  # 默认搜索关键词
    MAX_RESULTS_PER_REQUEST = 1000  # GitHub API最大结果数
    
    # 分页配置
    PROJECTS_PER_PAGE = 20
    
    # 缓存配置
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300 