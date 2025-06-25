from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_apscheduler import APScheduler
from config import Config

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
scheduler = APScheduler()

def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 初始化调度器
    scheduler.init_app(app)
    scheduler.start()
    
    # 注册蓝图
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 初始化定时任务
    from app.scheduler_init import init_scheduler
    init_scheduler(app)
    
    return app

def create_minimal_app(config_class=Config):
    """创建轻量级应用实例，仅用于数据库操作，不初始化scheduler"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 只初始化数据库相关扩展
    db.init_app(app)
    
    return app

# 导入模型（避免循环导入）
from app import models 