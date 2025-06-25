from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from app import db
from app.services import ProjectService, RefreshService, SchedulerService
from app.models import GitHubProject, RefreshLog, SchedulerConfig

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """首页"""
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '')
    owner = request.args.get('owner', '')
    language = request.args.get('language', '')
    sort_by = request.args.get('sort', 'stars_count')
    order = request.args.get('order', 'desc')
    
    # 获取每页项目数配置
    per_page = current_app.config.get('PROJECTS_PER_PAGE', 20)
    
    # 搜索项目
    pagination = ProjectService.search_projects(
        keyword=keyword if keyword else None,
        owner=owner if owner else None,
        language=language if language else None,
        sort_by=sort_by,
        order=order,
        page=page,
        per_page=per_page
    )
    
    # 获取所有可用的编程语言（用于筛选下拉框）
    languages = db.session.query(GitHubProject.language).distinct().filter(
        GitHubProject.language.isnot(None)
    ).order_by(GitHubProject.language).all()
    languages = [lang[0] for lang in languages if lang[0]]
    
    # 获取最近的刷新日志
    latest_refresh = RefreshLog.query.order_by(RefreshLog.created_at.desc()).first()
    
    return render_template('index.html',
                         projects=pagination.items,
                         pagination=pagination,
                         keyword=keyword,
                         owner=owner,
                         language=language,
                         languages=languages,
                         sort_by=sort_by,
                         order=order,
                         latest_refresh=latest_refresh)

@bp.route('/refresh')
def manual_refresh():
    """手动刷新"""
    keyword = request.args.get('keyword', current_app.config['DEFAULT_SEARCH_KEYWORD'])
    
    try:
        refresh_log = RefreshService.manual_refresh(keyword)
        if refresh_log.status == 'success':
            flash(f'刷新成功！新增 {refresh_log.new_projects} 个项目，更新 {refresh_log.updated_projects} 个项目', 'success')
        else:
            flash(f'刷新失败：{refresh_log.error_message}', 'error')
    except Exception as e:
        flash(f'刷新过程中发生错误：{str(e)}', 'error')
    
    return redirect(url_for('main.index'))

@bp.route('/project/<int:project_id>')
def project_detail(project_id):
    """项目详情页"""
    project = GitHubProject.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)

@bp.route('/stats')
def stats():
    """统计页面"""
    from app.models import ApiStats
    from sqlalchemy import func
    
    # 项目统计
    total_projects = GitHubProject.query.count()
    total_stars = db.session.query(func.sum(GitHubProject.stars_count)).scalar() or 0
    total_forks = db.session.query(func.sum(GitHubProject.forks_count)).scalar() or 0
    
    # 语言统计
    language_stats = db.session.query(
        GitHubProject.language,
        func.count(GitHubProject.id).label('count'),
        func.sum(GitHubProject.stars_count).label('total_stars')
    ).filter(
        GitHubProject.language.isnot(None)
    ).group_by(GitHubProject.language).order_by(
        func.count(GitHubProject.id).desc()
    ).limit(10).all()
    
    # 最近刷新日志
    recent_refreshes = RefreshLog.query.order_by(
        RefreshLog.created_at.desc()
    ).limit(10).all()
    
    # API统计
    api_stats = ApiStats.query.order_by(ApiStats.date.desc()).limit(7).all()
    
    return render_template('stats.html',
                         total_projects=total_projects,
                         total_stars=total_stars,
                         total_forks=total_forks,
                         language_stats=language_stats,
                         recent_refreshes=recent_refreshes,
                         api_stats=api_stats)

@bp.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')

@bp.route('/scheduler')
def scheduler_config():
    """定时器配置页面"""
    try:
        configs = SchedulerService.get_all_configs()
        scheduler_status = SchedulerService.get_scheduler_status()
        
        return render_template('scheduler_config.html', 
                             configs=configs, 
                             scheduler_status=scheduler_status)
    except Exception as e:
        flash(f'加载定时器配置失败：{str(e)}', 'error')
        return redirect(url_for('main.index'))

@bp.route('/scheduler/create', methods=['GET', 'POST'])
def create_scheduler_config():
    """创建定时器配置"""
    if request.method == 'GET':
        return render_template('scheduler_form.html', config=None, action='create')
    
    try:
        config_data = {
            'config_name': request.form.get('config_name'),
            'schedule_type': request.form.get('schedule_type'),
            'keyword': request.form.get('keyword', 'AI'),
            'description': request.form.get('description', ''),
            'max_results': int(request.form.get('max_results', 1000)),
            'is_active': 'is_active' in request.form
        }
        
        # 根据调度类型设置参数
        if config_data['schedule_type'] == 'interval':
            config_data['interval_hours'] = int(request.form.get('interval_hours', 6))
        elif config_data['schedule_type'] == 'cron':
            config_data['cron_hour'] = int(request.form.get('cron_hour', 0))
            config_data['cron_minute'] = int(request.form.get('cron_minute', 0))
            config_data['cron_day_of_week'] = request.form.get('cron_day_of_week', '*')
        
        config = SchedulerService.create_config(config_data)
        flash(f'定时器配置"{config.config_name}"创建成功！', 'success')
        return redirect(url_for('main.scheduler_config'))
        
    except Exception as e:
        flash(f'创建定时器配置失败：{str(e)}', 'error')
        return render_template('scheduler_form.html', config=None, action='create')

@bp.route('/scheduler/edit/<int:config_id>', methods=['GET', 'POST'])
def edit_scheduler_config(config_id):
    """编辑定时器配置"""
    config = SchedulerConfig.query.get_or_404(config_id)
    
    if request.method == 'GET':
        return render_template('scheduler_form.html', config=config, action='edit')
    
    try:
        config_data = {
            'config_name': request.form.get('config_name'),
            'schedule_type': request.form.get('schedule_type'),
            'keyword': request.form.get('keyword', 'AI'),
            'description': request.form.get('description', ''),
            'max_results': int(request.form.get('max_results', 1000)),
            'is_active': 'is_active' in request.form
        }
        
        # 根据调度类型设置参数
        if config_data['schedule_type'] == 'interval':
            config_data['interval_hours'] = int(request.form.get('interval_hours', 6))
        elif config_data['schedule_type'] == 'cron':
            config_data['cron_hour'] = int(request.form.get('cron_hour', 0))
            config_data['cron_minute'] = int(request.form.get('cron_minute', 0))
            config_data['cron_day_of_week'] = request.form.get('cron_day_of_week', '*')
        
        updated_config = SchedulerService.update_config(config_id, config_data)
        flash(f'定时器配置"{updated_config.config_name}"更新成功！', 'success')
        return redirect(url_for('main.scheduler_config'))
        
    except Exception as e:
        flash(f'更新定时器配置失败：{str(e)}', 'error')
        return render_template('scheduler_form.html', config=config, action='edit')

@bp.route('/scheduler/delete/<int:config_id>', methods=['POST'])
def delete_scheduler_config(config_id):
    """删除定时器配置"""
    try:
        config = SchedulerConfig.query.get_or_404(config_id)
        config_name = config.config_name
        
        SchedulerService.delete_config(config_id)
        flash(f'定时器配置"{config_name}"删除成功！', 'success')
        
    except Exception as e:
        flash(f'删除定时器配置失败：{str(e)}', 'error')
    
    return redirect(url_for('main.scheduler_config'))

@bp.route('/scheduler/toggle/<int:config_id>', methods=['POST'])
def toggle_scheduler_config(config_id):
    """切换定时器配置状态"""
    try:
        config = SchedulerService.toggle_config_status(config_id)
        status_text = '启用' if config.is_active else '禁用'
        flash(f'定时器配置"{config.config_name}"已{status_text}！', 'success')
        
    except Exception as e:
        flash(f'切换定时器状态失败：{str(e)}', 'error')
    
    return redirect(url_for('main.scheduler_config'))

@bp.route('/scheduler/execute/<int:config_id>', methods=['POST'])
def execute_scheduler_config(config_id):
    """立即执行定时器配置"""
    try:
        refresh_log = SchedulerService.execute_config_now(config_id)
        
        if refresh_log.status == 'success':
            flash(f'任务执行成功！新增 {refresh_log.new_projects} 个项目，更新 {refresh_log.updated_projects} 个项目', 'success')
        else:
            flash(f'任务执行失败：{refresh_log.error_message}', 'error')
        
    except Exception as e:
        flash(f'执行任务失败：{str(e)}', 'error')
    
    return redirect(url_for('main.scheduler_config'))

# 错误处理
@bp.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500 