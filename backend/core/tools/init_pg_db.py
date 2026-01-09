import psycopg2
from psycopg2 import OperationalError

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
pre_parent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, pre_parent_dir)

from config import Settings

class PostgresDB:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.conn = self.connect_postgres(settings)

    # 2. 封装数据库操作函数
    def connect_postgres(self,settings: Settings):

        # 1. 定义数据库连接参数
        db_params = {
            "host": settings.pg.host,    # Docker 宿主机 IP
            "port": settings.pg.port,           # 映射的端口
            "user": settings.pg.user,       # 自定义用户名
            "password": settings.pg.password, # 自定义密码
            "database": settings.pg.database      # 初始化的数据库名
        }

        """创建数据库连接"""
        conn = None
        try:
            # 建立连接
            conn = psycopg2.connect(**db_params)
            print("✅ 成功连接到 PostgreSQL 数据库")
            return conn
        except OperationalError as e:
            print(f"❌ 连接数据库失败: {e}")
            return None

    def create_table(self):
        """创建测试表"""
        try:
            # 创建游标（用于执行SQL）
            cur = self.conn.cursor()
            # 定义建表SQL
            create_sql = """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                age INT,
                email VARCHAR(100) UNIQUE,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            cur.execute(create_sql)
            self.conn.commit()  # 提交事务
            cur.close()
            print("✅ 表创建成功（或已存在）")
        except Exception as e:
            print(f"❌ 创建表失败: {e}")
            self.conn.rollback()  # 出错回滚

    def insert_data(self, name, age, email):
        """插入单条数据"""
        try:
            cur = self.conn.cursor()
            insert_sql = """
            INSERT INTO users (name, age, email) VALUES (%s, %s, %s);
            """
            # 使用 %s 作为占位符（psycopg2 标准写法，避免 SQL 注入）
            cur.execute(insert_sql, (name, age, email))
            self.conn.commit()
            cur.close()
            print(f"✅ 插入数据成功: {name}")
        except Exception as e:
            print(f"❌ 插入数据失败: {e}")
            self.conn.rollback()

    def query_data(self):
        """查询所有数据"""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM users;")
            # 获取所有查询结果
            rows = cur.fetchall()
            # 获取列名（方便展示）
            col_names = [desc[0] for desc in cur.description]
            cur.close()
            
            print("\n📋 查询结果:")
            print(col_names)
            for row in rows:
                print(row)
            return rows
        except Exception as e:
            print(f"❌ 查询数据失败: {e}")
            return None

    def delete_data(self):
        """删除所有测试数据"""
        try:
            cur = self.conn.cursor()
            cur.execute("DROP TABLE IF EXISTS users;")
            self.conn.commit()
            cur.close()
            print("✅ 所有测试数据已删除")
        except Exception as e:
            print(f"❌ 删除数据失败: {e}")
            self.conn.rollback()

    def close(self):
        """关闭数据库连接"""
        self.conn.close()
        print("\n🔌 数据库连接已关闭")

# 3. 主程序执行
if __name__ == "__main__":
    settings = Settings()
    # 建立连接
    pg = PostgresDB(settings)
    if pg.conn:
        # 创建表
        pg.create_table()
        # 插入测试数据
        pg.insert_data( "张三01", 35, "zhangsa01n@example.com")
        pg.insert_data( "李四02", 40, "lisi02@example.com")
        # 查询数据
        pg.query_data()

        # 删除测试数据
        pg.delete_data()
        
        # 关闭连接（重要：避免资源泄漏）
        pg.close()
        print("\n🔌 数据库连接已关闭")
