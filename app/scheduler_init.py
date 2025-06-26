from flask import current_app
from app.services import SchedulerService
from datetime import datetime, timezone, timedelta

# 中国时区 (UTC+8)
CHINA_TZ = timezone(timedelta(hours=8))

def china_now():
    """获取当前中国时间"""
    return datetime.now(CHINA_TZ).replace(tzinfo=None)

def init_scheduler(app):
    """初始化定时任务系统"""
    
    def setup_scheduler():
        """设置调度器"""
        try:
            # 创建默认配置（如果不存在）
            from app.models import SchedulerConfig
            
            # 检查是否存在默认配置
            default_config = SchedulerConfig.query.filter_by(config_name='默认定时任务').first()
            
            if not default_config:
                # 创建默认的定时配置
                default_data = {
                    'config_name': '默认定时任务',
                    'schedule_type': 'interval',
                    'interval_hours': app.config.get('REFRESH_INTERVAL_HOURS', 6),
                    'keyword': app.config.get('DEFAULT_SEARCH_KEYWORD', 'AI'),
                    'description': '系统默认的定时刷新任务，每6小时执行一次',
                    'is_active': True
                }
                
                # 只创建配置，不立即加载调度器
                from app.models import SchedulerConfig
                from app import db
                config = SchedulerConfig(**default_data)
                db.session.add(config)
                db.session.commit()
                app.logger.info("Created default scheduler config")
            
            app.logger.info("Scheduler initialized, use reload API to activate")
                
        except Exception as e:
            app.logger.error(f"Failed to initialize scheduler: {str(e)}")
    
    # 在应用上下文中执行设置
    with app.app_context():
        setup_scheduler()

def reload_all_schedules():
    """重新加载所有调度任务"""
    try:
        SchedulerService.reload_scheduler()
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to reload schedules: {str(e)}")
        return False

def get_scheduler_info():
    """获取调度器信息"""
    try:
        return SchedulerService.get_scheduler_status()
    except Exception as e:
        current_app.logger.error(f"Failed to get scheduler info: {str(e)}")
        return {'error': str(e)}

def add_one_time_task(task_name, func, run_at):
    """添加一次性任务"""
    try:
        app_scheduler = current_app.extensions['apscheduler']
        app_scheduler.add_job(
            func=func,
            trigger='date',
            run_date=run_at,
            id=f'onetime_{task_name}',
            replace_existing=True
        )
        current_app.logger.info(f"Added one-time task: {task_name} at {run_at}")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to add one-time task: {str(e)}")
        return False

def remove_job_by_id(job_id):
    """根据ID移除任务"""
    try:
        app_scheduler = current_app.extensions['apscheduler']
        app_scheduler.remove_job(job_id)
        current_app.logger.info(f"Removed job: {job_id}")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to remove job {job_id}: {str(e)}")
        return False 