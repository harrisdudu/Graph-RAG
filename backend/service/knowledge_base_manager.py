from sqlalchemy import create_engine, Column, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
import os

# 创建数据库连接
# 使用SQLite作为临时数据库，方便测试
DATABASE_URL = "sqlite:///./data/knowledge_base.db"

# 创建数据存储目录
os.makedirs(os.path.dirname(DATABASE_URL.replace("sqlite:///", "")), exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 知识库表模型
class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

# 创建数据库表
Base.metadata.create_all(bind=engine)

class KnowledgeBaseManager:
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        self.db.close()
    
    def create_knowledge_base(self, name, description=""):
        """创建知识库"""
        try:
            knowledge_base = KnowledgeBase(name=name, description=description)
            self.db.add(knowledge_base)
            self.db.commit()
            self.db.refresh(knowledge_base)
            return knowledge_base
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_knowledge_base(self, kb_id):
        """根据ID获取知识库"""
        return self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id, KnowledgeBase.is_active == True).first()
    
    def get_all_knowledge_bases(self):
        """获取所有活跃的知识库"""
        return self.db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True).all()
    
    def update_knowledge_base(self, kb_id, name=None, description=None):
        """更新知识库信息"""
        try:
            knowledge_base = self.get_knowledge_base(kb_id)
            if not knowledge_base:
                return None
            
            if name is not None:
                knowledge_base.name = name
            if description is not None:
                knowledge_base.description = description
            
            self.db.commit()
            self.db.refresh(knowledge_base)
            return knowledge_base
        except Exception as e:
            self.db.rollback()
            raise e
    
    def delete_knowledge_base(self, kb_id):
        """删除知识库(软删除)"""
        try:
            knowledge_base = self.get_knowledge_base(kb_id)
            if not knowledge_base:
                return None
            
            knowledge_base.is_active = False
            self.db.commit()
            return knowledge_base
        except Exception as e:
            self.db.rollback()
            raise e
    
    def hard_delete_knowledge_base(self, kb_id):
        """彻底删除知识库"""
        try:
            knowledge_base = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
            if not knowledge_base:
                return None
            
            self.db.delete(knowledge_base)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e