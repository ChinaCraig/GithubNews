#!/usr/bin/env python3
"""
GitHub新闻项目启动脚本
支持开发和生产环境
"""

import os
import sys
from app import create_app

def main():
    """主函数"""
    # 创建Flask应用
    app = create_app()
    
    # 获取环境变量
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    
    print(f"=== GitHub新闻项目 ===")
    print(f"环境: {'开发' if debug_mode else '生产'}")
    print(f"地址: http://{host}:{port}")
    print(f"调试模式: {debug_mode}")
    print("=" * 30)
    
    try:
        # 启动应用
        app.run(
            host=host,
            port=port,
            debug=debug_mode,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 