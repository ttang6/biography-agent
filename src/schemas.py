"""
Pydantic 数据模型

定义 API 请求/响应的数据格式
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel


# ============ 项目相关 ============

class ProjectCreate(BaseModel):
    """创建项目的请求"""
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """项目信息响应"""
    id: UUID
    name: str
    description: Optional[str]
    status: str
    current_agent: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ 对话相关 ============

class DialogueItem(BaseModel):
    """单条对话"""
    speaker: str          # 说话人：记者 / 受访者
    text: str             # 对话内容
    emotion: Optional[str] = None  # 情绪：平静、激动、沉默等
    start_time: Optional[float] = None  # 开始时间（秒）
    end_time: Optional[float] = None    # 结束时间（秒）


class CleanDialogue(BaseModel):
    """清洗后的完整对话"""
    dialogues: List[DialogueItem]
    metadata: Dict[str, Any] = {}  # 元数据：总时长、说话人数量等


# ============ 蓝图相关 ============

class ChapterPlan(BaseModel):
    """章节规划"""
    chapter_id: str
    title: str            # 章节标题
    theme: str            # 主题
    target_words: int = 2000  # 目标字数
    key_points: List[str] = []  # 要点


class NarrativeBlueprint(BaseModel):
    """叙事蓝图"""
    title: str            # 文章总标题
    chapters: List[ChapterPlan]
    style: str = "文学性非虚构"  # 写作风格


# ============ 文章相关 ============

class Footnote(BaseModel):
    """注释"""
    marker: str           # 标记，如 [注一]
    content: str          # 注释内容


class AuditReport(BaseModel):
    """审计报告"""
    fact_coverage: float = 0.0  # 事实覆盖率
    violations: List[str] = []   # 违规项


class ArticleResponse(BaseModel):
    """文章响应"""
    id: UUID
    title: Optional[str]
    content: str
    footnotes: List[Footnote] = []
    audit_report: Optional[AuditReport] = None
    word_count: Optional[int]
    version: int
    created_at: datetime
    
    class Config:
        from_attributes = True
