from flask import current_app
from app.services import RefreshService
from app import scheduler
from datetime import datetime

def init_scheduler(app):
    """初始化定时任务"""
    
    @scheduler.task('interval', id='scheduled_refresh', hours=app.config['REFRESH_INTERVAL_HOURS'])
    def scheduled_refresh():
        """定时刷新任务"""
        with app.app_context():
            try:
                current_app.logger.info("Starting scheduled refresh...")
                refresh_log = RefreshService.scheduled_refresh()
                current_app.logger.info(f"Scheduled refresh completed: {refresh_log.status}")
            except Exception as e:
                current_app.logger.error(f"Scheduled refresh failed: {str(e)}")
    
    # 启动时执行一次刷新（可选）
    @scheduler.task('interval', id='startup_refresh', seconds=30)
    def startup_refresh():
        """启动时刷新任务（只执行一次）"""
        with app.app_context():
            try:
                # 检查是否已经执行过启动刷新
                from app.models import RefreshLog
                today = datetime.now().date()
                startup_refresh_today = RefreshLog.query.filter(
                    RefreshLog.refresh_type == 'scheduled',
                    RefreshLog.start_time >= today
                ).first()
                
                if not startup_refresh_today:
                    current_app.logger.info("Starting startup refresh...")
                    refresh_log = RefreshService.scheduled_refresh()
                    current_app.logger.info(f"Startup refresh completed: {refresh_log.status}")
                
                # 移除这个一次性任务
                scheduler.remove_job('startup_refresh')
                
            except Exception as e:
                current_app.logger.error(f"Startup refresh failed: {str(e)}")
                # 移除任务即使失败了
                try:
                    scheduler.remove_job('startup_refresh')
                except:
                    pass 