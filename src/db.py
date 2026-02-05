"""
数据库模型和连接

这个文件包含：
1. 数据库连接配置
2. 所有数据表的定义
"""

import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# ============ 数据库连接 ============

# 连接字符串：postgresql://用户名:密码@主机:端口/数据库名
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/bio_agent"

# 创建数据库引擎
engine = create_engine(DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(bind=engine)

# 模型基类
Base = declarative_base()


def get_db():
    """获取数据库会话（FastAPI 依赖注入用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============ 数据表定义 ============

class Project(Base):
    """项目表 - 每个采访项目一条记录"""
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, comment="项目名称")
    description = Column(Text, comment="项目描述")
    
    # 状态机：INITIALIZED -> TRANSCRIBING -> PLANNING -> WRITING -> COMPLETED
    status = Column(String(50), default="INITIALIZED", comment="当前状态")
    current_agent = Column(String(50), comment="当前处理的 Agent")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    audio_files = relationship("AudioFile", back_populates="project")
    dialogues = relationship("Dialogue", back_populates="project")
    blueprints = relationship("Blueprint", back_populates="project")
    articles = relationship("Article", back_populates="project")


class AudioFile(Base):
    """音频文件表"""
    __tablename__ = "audio_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    filename = Column(String(255), nullable=False, comment="文件名")
    file_path = Column(Text, nullable=False, comment="文件路径")
    duration = Column(Float, comment="时长（秒）")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="audio_files")


class Dialogue(Base):
    """对话表 - 存储清洗后的采访对话"""
    __tablename__ = "dialogues"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    # 对话内容（JSON 格式）
    # 结构：{"dialogues": [{"speaker": "记者", "text": "...", "emotion": "平静"}], "metadata": {...}}
    content = Column(JSONB, nullable=False, comment="对话内容 JSON")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="dialogues")


class Blueprint(Base):
    """叙事蓝图表 - 存储章节规划"""
    __tablename__ = "blueprints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    # 蓝图内容（JSON 格式）
    # 结构：{"title": "...", "chapters": [{"title": "童年", "theme": "成长"}]}
    content = Column(JSONB, nullable=False, comment="蓝图内容 JSON")
    
    version = Column(Integer, default=1, comment="版本号")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="blueprints")


class Article(Base):
    """文章表 - 存储生成的文章"""
    __tablename__ = "articles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    title = Column(String(500), comment="文章标题")
    content = Column(Text, nullable=False, comment="文章正文（Markdown）")
    
    # 注释（JSON 数组）
    footnotes = Column(JSONB, default=list, comment="注释列表")
    
    # 审计报告（JSON）
    audit_report = Column(JSONB, default=dict, comment="审计报告")
    
    word_count = Column(Integer, comment="字数")
    version = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="articles")


def init_db():
    """创建所有数据表"""
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")
