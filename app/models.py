from datetime import datetime, timezone, timedelta
from app import db
import json

# 中国时区 (UTC+8)
CHINA_TZ = timezone(timedelta(hours=8))

def china_now():
    """获取当前中国时间"""
    return datetime.now(CHINA_TZ).replace(tzinfo=None)

class GitHubProject(db.Model):
    """GitHub项目模型"""
    __tablename__ = 'github_projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, comment='项目名称')
    full_name = db.Column(db.String(255), nullable=False, comment='完整项目名称')
    owner = db.Column(db.String(255), nullable=False, comment='项目作者')
    description = db.Column(db.Text, comment='项目简介')
    html_url = db.Column(db.String(500), nullable=False, comment='GitHub项目地址')
    stars_count = db.Column(db.Integer, default=0, comment='星标数量')
    forks_count = db.Column(db.Integer, default=0, comment='分叉数量')
    watchers_count = db.Column(db.Integer, default=0, comment='关注者数量')
    language = db.Column(db.String(100), comment='主要编程语言')
    topics = db.Column(db.JSON, comment='项目主题标签')
    license_name = db.Column(db.String(100), comment='许可证名称')
    default_branch = db.Column(db.String(100), default='main', comment='默认分支')
    is_private = db.Column(db.Boolean, default=False, comment='是否私有项目')
    is_fork = db.Column(db.Boolean, default=False, comment='是否为分叉项目')
    created_at = db.Column(db.DateTime, comment='GitHub上的创建时间')
    updated_at = db.Column(db.DateTime, comment='GitHub上的更新时间')
    pushed_at = db.Column(db.DateTime, comment='最后推送时间')
    size_kb = db.Column(db.Integer, default=0, comment='项目大小(KB)')
    open_issues_count = db.Column(db.Integer, default=0, comment='开放问题数量')
    has_issues = db.Column(db.Boolean, default=True, comment='是否开启Issues')
    has_projects = db.Column(db.Boolean, default=True, comment='是否开启Projects')
    has_wiki = db.Column(db.Boolean, default=True, comment='是否开启Wiki')
    archived = db.Column(db.Boolean, default=False, comment='是否已归档')
    disabled = db.Column(db.Boolean, default=False, comment='是否已禁用')
    visibility = db.Column(db.String(20), default='public', comment='可见性')
    
    # 本地管理字段
    local_created_at = db.Column(db.TIMESTAMP, default=china_now, comment='本地创建时间')
    local_updated_at = db.Column(db.TIMESTAMP, default=china_now, onupdate=china_now, comment='本地更新时间')
    last_fetched_at = db.Column(db.TIMESTAMP, default=china_now, comment='最后抓取时间')
    fetch_count = db.Column(db.Integer, default=1, comment='抓取次数')
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('name', 'owner', name='unique_project'),
        db.Index('idx_full_name', 'full_name'),
        db.Index('idx_owner', 'owner'),
        db.Index('idx_stars', 'stars_count'),
        db.Index('idx_language', 'language'),
        db.Index('idx_updated_at', 'updated_at'),
    )
    
    def __repr__(self):
        return f'<GitHubProject {self.full_name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'full_name': self.full_name,
            'owner': self.owner,
            'description': self.description,
            'html_url': self.html_url,
            'stars_count': self.stars_count,
            'forks_count': self.forks_count,
            'watchers_count': self.watchers_count,
            'language': self.language,
            'topics': self.topics,
            'license_name': self.license_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'pushed_at': self.pushed_at.isoformat() if self.pushed_at else None,
            'local_updated_at': self.local_updated_at.isoformat() if self.local_updated_at else None,
        }

class RefreshLog(db.Model):
    """刷新日志模型"""
    __tablename__ = 'refresh_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    refresh_type = db.Column(db.Enum('manual', 'scheduled'), nullable=False, comment='刷新类型')
    keyword = db.Column(db.String(255), nullable=False, comment='搜索关键词')
    total_fetched = db.Column(db.Integer, default=0, comment='获取的项目总数')
    new_projects = db.Column(db.Integer, default=0, comment='新增项目数')
    updated_projects = db.Column(db.Integer, default=0, comment='更新项目数')
    start_time = db.Column(db.TIMESTAMP, nullable=False, comment='开始时间')
    end_time = db.Column(db.TIMESTAMP, comment='结束时间')
    duration_seconds = db.Column(db.Integer, default=0, comment='耗时(秒)')
    status = db.Column(db.Enum('running', 'success', 'failed'), default='running', comment='状态')
    error_message = db.Column(db.Text, comment='错误信息')
    api_requests_count = db.Column(db.Integer, default=0, comment='API请求次数')
    created_at = db.Column(db.TIMESTAMP, default=china_now)
    
    def __repr__(self):
        return f'<RefreshLog {self.refresh_type} {self.keyword}>'

class SystemConfig(db.Model):
    """系统配置模型"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False, comment='配置键')
    config_value = db.Column(db.Text, comment='配置值')
    description = db.Column(db.String(255), comment='配置描述')
    config_type = db.Column(db.Enum('string', 'int', 'float', 'boolean', 'json'), default='string', comment='配置类型')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.TIMESTAMP, default=china_now)
    updated_at = db.Column(db.TIMESTAMP, default=china_now, onupdate=china_now)
    
    def __repr__(self):
        return f'<SystemConfig {self.config_key}>'
    
    def get_value(self):
        """根据类型返回配置值"""
        if not self.config_value:
            return None
            
        if self.config_type == 'int':
            return int(self.config_value)
        elif self.config_type == 'float':
            return float(self.config_value)
        elif self.config_type == 'boolean':
            return self.config_value.lower() in ('true', '1', 'yes', 'on')
        elif self.config_type == 'json':
            return json.loads(self.config_value)
        else:
            return self.config_value

class ApiStats(db.Model):
    """API请求统计模型"""
    __tablename__ = 'api_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False, comment='日期')
    total_requests = db.Column(db.Integer, default=0, comment='总请求数')
    successful_requests = db.Column(db.Integer, default=0, comment='成功请求数')
    failed_requests = db.Column(db.Integer, default=0, comment='失败请求数')
    rate_limit_hits = db.Column(db.Integer, default=0, comment='触发限制次数')
    created_at = db.Column(db.TIMESTAMP, default=china_now)
    updated_at = db.Column(db.TIMESTAMP, default=china_now, onupdate=china_now)
    
    def __repr__(self):
        return f'<ApiStats {self.date}>'

class SchedulerConfig(db.Model):
    """定时器配置模型"""
    __tablename__ = 'scheduler_config'
    
    id = db.Column(db.Integer, primary_key=True)
    config_name = db.Column(db.String(100), unique=True, nullable=False, comment='配置名称')
    schedule_type = db.Column(db.Enum('interval', 'cron'), nullable=False, default='interval', comment='调度类型：interval=固定间隔，cron=指定时间')
    
    # 固定间隔配置
    interval_hours = db.Column(db.Integer, comment='间隔小时数（仅interval类型使用）')
    
    # 指定时间配置
    cron_hour = db.Column(db.Integer, comment='小时（0-23，仅cron类型使用）')
    cron_minute = db.Column(db.Integer, default=0, comment='分钟（0-59，仅cron类型使用）')
    cron_day_of_week = db.Column(db.String(20), comment='星期几（0-6或*，仅cron类型使用）')
    
    # 通用配置
    keyword = db.Column(db.String(255), default='AI', comment='搜索关键词')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    max_results = db.Column(db.Integer, default=1000, comment='最大结果数')
    
    # 元数据
    description = db.Column(db.String(500), comment='配置描述')
    created_at = db.Column(db.TIMESTAMP, default=china_now)
    updated_at = db.Column(db.TIMESTAMP, default=china_now, onupdate=china_now)
    last_executed = db.Column(db.TIMESTAMP, comment='最后执行时间')
    
    def __repr__(self):
        return f'<SchedulerConfig {self.config_name}>'
    
    def get_schedule_expression(self):
        """获取调度表达式"""
        if self.schedule_type == 'interval':
            return f"每{self.interval_hours}小时执行一次"
        elif self.schedule_type == 'cron':
            day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            if self.cron_day_of_week == '*':
                day_desc = '每天'
            else:
                days = [day_names[int(d)] for d in self.cron_day_of_week.split(',')]
                day_desc = '、'.join(days)
            return f"{day_desc} {self.cron_hour:02d}:{self.cron_minute:02d}"
        return "未知调度类型"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'config_name': self.config_name,
            'schedule_type': self.schedule_type,
            'interval_hours': self.interval_hours,
            'cron_hour': self.cron_hour,
            'cron_minute': self.cron_minute,
            'cron_day_of_week': self.cron_day_of_week,
            'keyword': self.keyword,
            'is_active': self.is_active,
            'max_results': self.max_results,
            'description': self.description,
            'schedule_expression': self.get_schedule_expression(),
            'last_executed': self.last_executed.isoformat() if self.last_executed else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 