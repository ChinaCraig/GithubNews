from flask import Blueprint, jsonify, request, current_app
from app import db
from app.services import ProjectService, RefreshService
from app.models import GitHubProject, RefreshLog, ApiStats
from datetime import datetime, timedelta

bp = Blueprint('api', __name__)

@bp.route('/projects')
def api_projects():
    """获取项目列表API"""
    try:
        page = request.args.get('page', 1, type=int)
        keyword = request.args.get('keyword')
        owner = request.args.get('owner')
        language = request.args.get('language')
        sort_by = request.args.get('sort', 'stars_count')
        order = request.args.get('order', 'desc')
        per_page = request.args.get('per_page', 20, type=int)
        
        # 限制每页最大数量
        per_page = min(per_page, 100)
        
        pagination = ProjectService.search_projects(
            keyword=keyword,
            owner=owner,
            language=language,
            sort_by=sort_by,
            order=order,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'projects': [project.to_dict() for project in pagination.items],
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next,
                    'prev_num': pagination.prev_num,
                    'next_num': pagination.next_num
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/projects/<int:project_id>')
def api_project_detail(project_id):
    """获取项目详情API"""
    try:
        project = GitHubProject.query.get(project_id)
        if not project:
            return jsonify({
                'status': 'error',
                'message': 'Project not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': project.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/refresh', methods=['POST'])
def api_refresh():
    """手动刷新API"""
    try:
        data = request.get_json() or {}
        keyword = data.get('keyword', current_app.config['DEFAULT_SEARCH_KEYWORD'])
        
        refresh_log = RefreshService.manual_refresh(keyword)
        
        return jsonify({
            'status': 'success',
            'data': {
                'refresh_id': refresh_log.id,
                'status': refresh_log.status,
                'keyword': refresh_log.keyword,
                'new_projects': refresh_log.new_projects,
                'updated_projects': refresh_log.updated_projects,
                'total_fetched': refresh_log.total_fetched,
                'duration_seconds': refresh_log.duration_seconds,
                'error_message': refresh_log.error_message
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/refresh/status/<int:refresh_id>')
def api_refresh_status(refresh_id):
    """获取刷新状态API"""
    try:
        refresh_log = RefreshLog.query.get(refresh_id)
        if not refresh_log:
            return jsonify({
                'status': 'error',
                'message': 'Refresh log not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': refresh_log.id,
                'refresh_type': refresh_log.refresh_type,
                'keyword': refresh_log.keyword,
                'status': refresh_log.status,
                'new_projects': refresh_log.new_projects,
                'updated_projects': refresh_log.updated_projects,
                'total_fetched': refresh_log.total_fetched,
                'start_time': refresh_log.start_time.isoformat() if refresh_log.start_time else None,
                'end_time': refresh_log.end_time.isoformat() if refresh_log.end_time else None,
                'duration_seconds': refresh_log.duration_seconds,
                'error_message': refresh_log.error_message
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/stats')
def api_stats():
    """获取统计信息API"""
    try:
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
        
        # 最近刷新统计
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        recent_refreshes = RefreshLog.query.filter(
            RefreshLog.start_time >= week_ago
        ).count()
        
        successful_refreshes = RefreshLog.query.filter(
            RefreshLog.start_time >= week_ago,
            RefreshLog.status == 'success'
        ).count()
        
        return jsonify({
            'status': 'success',
            'data': {
                'projects': {
                    'total': total_projects,
                    'total_stars': total_stars,
                    'total_forks': total_forks
                },
                'languages': [
                    {
                        'language': lang[0],
                        'count': lang[1],
                        'total_stars': lang[2] or 0
                    }
                    for lang in language_stats
                ],
                'refreshes': {
                    'recent_count': recent_refreshes,
                    'successful_count': successful_refreshes,
                    'success_rate': round((successful_refreshes / recent_refreshes * 100) if recent_refreshes > 0 else 0, 2)
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/languages')
def api_languages():
    """获取所有编程语言列表API"""
    try:
        from sqlalchemy import func
        
        languages = db.session.query(
            GitHubProject.language,
            func.count(GitHubProject.id).label('count')
        ).filter(
            GitHubProject.language.isnot(None)
        ).group_by(GitHubProject.language).order_by(
            GitHubProject.language
        ).all()
        
        return jsonify({
            'status': 'success',
            'data': [
                {
                    'language': lang[0],
                    'count': lang[1]
                }
                for lang in languages
            ]
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# API错误处理
@bp.errorhandler(404)
def api_not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Resource not found'
    }), 404

@bp.errorhandler(500)
def api_internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500 