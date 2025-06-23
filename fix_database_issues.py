#!/usr/bin/env python3
"""
数据库问题修复脚本
解决description字段长度限制和其他数据库问题
"""

import sys
import pymysql
from config import Config

def fix_description_field():
    """修复description字段长度问题"""
    try:
        print("🔧 连接数据库...")
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            print("📋 检查当前description字段类型...")
            cursor.execute("DESCRIBE github_projects")
            columns = cursor.fetchall()
            
            for column in columns:
                if column[0] == 'description':
                    print(f"   当前类型: {column[1]}")
                    break
            
            print("🔄 修改description字段为LONGTEXT...")
            cursor.execute("ALTER TABLE github_projects MODIFY COLUMN description LONGTEXT COMMENT '项目简介'")
            
            print("✅ 字段修改成功！")
            
            # 验证修改结果
            cursor.execute("DESCRIBE github_projects")
            columns = cursor.fetchall()
            for column in columns:
                if column[0] == 'description':
                    print(f"   新类型: {column[1]}")
                    break
        
        connection.commit()
        connection.close()
        print("✅ 数据库修复完成")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

def clean_problematic_data():
    """清理可能有问题的数据"""
    try:
        print("🧹 清理过长的描述数据...")
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 查找描述过长的记录
            cursor.execute("SELECT COUNT(*) FROM github_projects WHERE CHAR_LENGTH(description) > 5000")
            long_desc_count = cursor.fetchone()[0]
            
            if long_desc_count > 0:
                print(f"   发现 {long_desc_count} 条过长描述记录")
                
                # 截断过长的描述
                cursor.execute("""
                    UPDATE github_projects 
                    SET description = CONCAT(LEFT(description, 4997), '...') 
                    WHERE CHAR_LENGTH(description) > 5000
                """)
                
                print(f"   已截断 {cursor.rowcount} 条记录的描述")
            else:
                print("   没有发现过长的描述")
        
        connection.commit()
        connection.close()
        print("✅ 数据清理完成")
        return True
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        return False

def test_database_health():
    """测试数据库健康状态"""
    try:
        print("🏥 检查数据库健康状态...")
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 检查表状态
            cursor.execute("SHOW TABLE STATUS LIKE 'github_projects'")
            status = cursor.fetchone()
            
            if status:
                print(f"   表名: {status[0]}")
                print(f"   存储引擎: {status[1]}")
                print(f"   行数: {status[4]:,}")
                print(f"   数据大小: {status[6] / 1024 / 1024:.2f} MB")
                print(f"   索引大小: {status[8] / 1024 / 1024:.2f} MB")
            
            # 检查字符集
            cursor.execute("SHOW CREATE TABLE github_projects")
            create_sql = cursor.fetchone()[1]
            print(f"   字符集: {'utf8mb4' if 'utf8mb4' in create_sql else '其他'}")
            
        connection.close()
        print("✅ 数据库状态正常")
        return True
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def main():
    """主修复流程"""
    print("=== GitHub新闻项目 - 数据库修复工具 ===")
    print()
    
    # 1. 检查数据库健康状态
    print("1️⃣ 检查数据库状态...")
    if not test_database_health():
        print("❌ 数据库连接失败，请检查配置")
        return 1
    print()
    
    # 2. 修复字段类型
    print("2️⃣ 修复description字段...")
    if not fix_description_field():
        print("❌ 字段修复失败")
        return 1
    print()
    
    # 3. 清理问题数据
    print("3️⃣ 清理问题数据...")
    if not clean_problematic_data():
        print("❌ 数据清理失败")
        return 1
    print()
    
    print("🎉 所有修复完成！")
    print("现在可以重新尝试手动刷新功能。")
    print()
    print("修复内容:")
    print("✅ description字段类型已改为LONGTEXT")
    print("✅ 过长的描述已自动截断")
    print("✅ 数据库会话错误处理已优化")
    print("✅ 主题标签数量已限制为20个")
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 