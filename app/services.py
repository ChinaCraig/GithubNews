import requests
import time
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models import GitHubProject, RefreshLog, SystemConfig, ApiStats
from sqlalchemy import and_, or_

class GitHubService:
    """GitHub API服务类"""
    
    def __init__(self):
        self.base_url = current_app.config['GITHUB_API_BASE_URL']
        self.token = current_app.config.get('GITHUB_TOKEN')
        self.headers = {
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'GitHub-News-App/1.0'
        }
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
    
    def search_repositories(self, keyword='AI', sort='stars', order='desc', per_page=100, page=1):
        """搜索仓库"""
        url = f"{self.base_url}/search/repositories"
        params = {
            'q': keyword,
            'sort': sort,
            'order': order,
            'per_page': per_page,
            'page': page
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            self._update_api_stats(response.status_code)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                # 处理API限制
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                wait_time = reset_time - int(time.time())
                if wait_time > 0:
                    current_app.logger.warning(f"API rate limit hit, waiting {wait_time} seconds")
                    time.sleep(wait_time + 10)  # 额外等待10秒
                return None
            else:
                current_app.logger.error(f"GitHub API error: {response.status_code}")
                return None
                
        except Exception as e:
            current_app.logger.error(f"Request error: {str(e)}")
            self._update_api_stats(0, failed=True)
            return None
    
    def fetch_all_repositories(self, keyword='AI', max_results=1000):
        """获取所有仓库（分页处理）"""
        all_repos = []
        page = 1
        per_page = 100
        
        while len(all_repos) < max_results:
            current_app.logger.info(f"Fetching page {page}")
            result = self.search_repositories(
                keyword=keyword, 
                sort='stars', 
                order='desc', 
                per_page=per_page, 
                page=page
            )
            
            if not result or 'items' not in result:
                break
                
            repos = result['items']
            if not repos:
                break
                
            all_repos.extend(repos)
            
            # GitHub API最多返回1000个结果
            if len(all_repos) >= result.get('total_count', 0) or page * per_page >= 1000:
                break
                
            page += 1
            time.sleep(1)  # 避免请求过快
        
        return all_repos[:max_results]
    
    def _update_api_stats(self, status_code, failed=False):
        """更新API统计"""
        today = datetime.now().date()
        stats = ApiStats.query.filter_by(date=today).first()
        
        if not stats:
            stats = ApiStats(date=today)
            db.session.add(stats)
        
        # 处理可能为None的统计字段
        if stats.total_requests is None:
            stats.total_requests = 0
        stats.total_requests += 1
        
        if failed or status_code >= 400:
            if stats.failed_requests is None:
                stats.failed_requests = 0
            stats.failed_requests += 1
            if status_code == 403:
                if stats.rate_limit_hits is None:
                    stats.rate_limit_hits = 0
                stats.rate_limit_hits += 1
        else:
            if stats.successful_requests is None:
                stats.successful_requests = 0
            stats.successful_requests += 1
        
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Failed to update API stats: {str(e)}")
            db.session.rollback()

class ProjectService:
    """项目管理服务类"""
    
    @staticmethod
    def save_projects(repos_data, refresh_log_id=None):
        """保存项目数据到数据库"""
        new_count = 0
        updated_count = 0
        
        for repo in repos_data:
            try:
                # 检查项目是否已存在
                existing_project = GitHubProject.query.filter_by(
                    name=repo['name'],
                    owner=repo['owner']['login']
                ).first()
                
                if existing_project:
                    # 更新现有项目
                    ProjectService._update_project(existing_project, repo)
                    updated_count += 1
                else:
                    # 创建新项目
                    ProjectService._create_project(repo)
                    new_count += 1
                
                # 立即提交当前项目，避免会话回滚影响其他项目
                db.session.flush()
                    
            except Exception as e:
                current_app.logger.error(f"Error saving project {repo.get('name', 'unknown')}: {str(e)}")
                # 回滚当前事务，继续处理下一个项目
                db.session.rollback()
                continue
        
        try:
            # 最终提交所有更改
            db.session.commit()
            current_app.logger.info(f"Saved {new_count} new projects, updated {updated_count} projects")
            
            # 更新刷新日志
            if refresh_log_id:
                refresh_log = RefreshLog.query.get(refresh_log_id)
                if refresh_log:
                    refresh_log.new_projects = new_count
                    refresh_log.updated_projects = updated_count
                    refresh_log.total_fetched = len(repos_data)
                    db.session.commit()
                    
        except Exception as e:
            current_app.logger.error(f"Error committing projects: {str(e)}")
            db.session.rollback()
            
        return new_count, updated_count
    
    @staticmethod
    def _create_project(repo):
        """创建新项目"""
        # 限制描述长度，避免数据库字段溢出
        description = repo.get('description', '') or ''
        if len(description) > 5000:  # 限制为5000字符
            description = description[:4997] + '...'
        
        project = GitHubProject(
            name=repo['name'],
            full_name=repo['full_name'],
            owner=repo['owner']['login'],
            description=description,
            html_url=repo['html_url'],
            stars_count=repo.get('stargazers_count', 0),
            forks_count=repo.get('forks_count', 0),
            watchers_count=repo.get('watchers_count', 0),
            language=repo.get('language'),
            topics=repo.get('topics', [])[:20],  # 限制主题标签数量
            license_name=repo.get('license', {}).get('name') if repo.get('license') else None,
            default_branch=repo.get('default_branch', 'main'),
            is_private=repo.get('private', False),
            is_fork=repo.get('fork', False),
            created_at=datetime.fromisoformat(repo['created_at'].replace('Z', '+00:00')) if repo.get('created_at') else None,
            updated_at=datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00')) if repo.get('updated_at') else None,
            pushed_at=datetime.fromisoformat(repo['pushed_at'].replace('Z', '+00:00')) if repo.get('pushed_at') else None,
            size_kb=repo.get('size', 0),
            open_issues_count=repo.get('open_issues_count', 0),
            has_issues=repo.get('has_issues', True),
            has_projects=repo.get('has_projects', True),
            has_wiki=repo.get('has_wiki', True),
            archived=repo.get('archived', False),
            disabled=repo.get('disabled', False),
            visibility=repo.get('visibility', 'public')
        )
        db.session.add(project)
    
    @staticmethod
    def _update_project(project, repo):
        """更新现有项目"""
        # 限制描述长度，避免数据库字段溢出
        description = repo.get('description', '') or ''
        if len(description) > 5000:  # 限制为5000字符
            description = description[:4997] + '...'
        
        project.description = description
        project.stars_count = repo.get('stargazers_count', 0)
        project.forks_count = repo.get('forks_count', 0)
        project.watchers_count = repo.get('watchers_count', 0)
        project.language = repo.get('language')
        project.topics = repo.get('topics', [])[:20]  # 限制主题标签数量
        project.license_name = repo.get('license', {}).get('name') if repo.get('license') else None
        project.updated_at = datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00')) if repo.get('updated_at') else None
        project.pushed_at = datetime.fromisoformat(repo['pushed_at'].replace('Z', '+00:00')) if repo.get('pushed_at') else None
        project.size_kb = repo.get('size', 0)
        project.open_issues_count = repo.get('open_issues_count', 0)
        project.archived = repo.get('archived', False)
        project.disabled = repo.get('disabled', False)
        project.last_fetched_at = datetime.utcnow()
        # 处理fetch_count可能为None的情况
        if project.fetch_count is None:
            project.fetch_count = 1
        else:
            project.fetch_count += 1
    
    @staticmethod
    def search_projects(keyword=None, owner=None, language=None, sort_by='stars_count', order='desc', page=1, per_page=20):
        """搜索项目"""
        query = GitHubProject.query
        
        # 构建搜索条件
        if keyword:
            query = query.filter(
                or_(
                    GitHubProject.name.contains(keyword),
                    GitHubProject.description.contains(keyword),
                    GitHubProject.full_name.contains(keyword)
                )
            )
        
        if owner:
            query = query.filter(GitHubProject.owner.contains(owner))
        
        if language:
            query = query.filter(GitHubProject.language == language)
        
        # 排序
        if sort_by == 'stars_count':
            if order == 'desc':
                query = query.order_by(GitHubProject.stars_count.desc())
            else:
                query = query.order_by(GitHubProject.stars_count.asc())
        elif sort_by == 'updated_at':
            if order == 'desc':
                query = query.order_by(GitHubProject.updated_at.desc())
            else:
                query = query.order_by(GitHubProject.updated_at.asc())
        elif sort_by == 'name':
            if order == 'desc':
                query = query.order_by(GitHubProject.name.desc())
            else:
                query = query.order_by(GitHubProject.name.asc())
        
        # 分页
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return pagination

class RefreshService:
    """刷新服务类"""
    
    @staticmethod
    def manual_refresh(keyword=None):
        """手动刷新"""
        if not keyword:
            keyword = current_app.config['DEFAULT_SEARCH_KEYWORD']
        
        return RefreshService._perform_refresh('manual', keyword)
    
    @staticmethod
    def scheduled_refresh():
        """定时刷新"""
        keyword = current_app.config['DEFAULT_SEARCH_KEYWORD']
        return RefreshService._perform_refresh('scheduled', keyword)
    
    @staticmethod
    def _perform_refresh(refresh_type, keyword):
        """执行刷新操作"""
        start_time = datetime.utcnow()
        
        # 创建刷新日志
        refresh_log = RefreshLog(
            refresh_type=refresh_type,
            keyword=keyword,
            start_time=start_time,
            status='running'
        )
        db.session.add(refresh_log)
        db.session.commit()
        
        try:
            # 获取GitHub数据
            github_service = GitHubService()
            max_results = current_app.config['MAX_RESULTS_PER_REQUEST']
            repos_data = github_service.fetch_all_repositories(keyword, max_results)
            
            if repos_data:
                # 保存到数据库
                new_count, updated_count = ProjectService.save_projects(repos_data, refresh_log.id)
                
                # 更新日志状态
                refresh_log.end_time = datetime.utcnow()
                refresh_log.duration_seconds = int((refresh_log.end_time - start_time).total_seconds())
                refresh_log.status = 'success'
                refresh_log.total_fetched = len(repos_data)
                refresh_log.new_projects = new_count
                refresh_log.updated_projects = updated_count
                
                current_app.logger.info(f"Refresh completed: {new_count} new, {updated_count} updated")
                
            else:
                refresh_log.status = 'failed'
                refresh_log.error_message = 'Failed to fetch data from GitHub API'
                
        except Exception as e:
            refresh_log.end_time = datetime.utcnow()
            refresh_log.duration_seconds = int((refresh_log.end_time - start_time).total_seconds())
            refresh_log.status = 'failed'
            refresh_log.error_message = str(e)
            current_app.logger.error(f"Refresh failed: {str(e)}")
        
        finally:
            try:
                db.session.commit()
            except Exception as e:
                current_app.logger.error(f"Failed to save refresh log: {str(e)}")
                db.session.rollback()
        
        return refresh_log 