"""
Bio-Agent 主程序

采访到叙事长文生成系统 - FastAPI 后端

运行方式：
    cd bio-agent
    uvicorn src.main:app --reload --port 8080
    
API 文档：
    http://localhost:8080/docs
"""

import os
import shutil
from pathlib import Path
from typing import List
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from src.db import get_db, init_db, Project, AudioFile, Dialogue, Blueprint, Article
from src.schemas import ProjectCreate, ProjectResponse, CleanDialogue, NarrativeBlueprint, ArticleResponse

# ============ 创建 FastAPI 应用 ============

app = FastAPI(
    title="Bio-Agent",
    description="故事生成系统",
    version="0.1.0"
)

# 允许跨域（前端访问用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 上传目录
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# ============ 启动时初始化数据库 ============

@app.on_event("startup")
def startup():
    print("🚀 Bio-Agent 启动中...")
    init_db()
    print(f"📁 上传目录: {UPLOAD_DIR}")
    print("✅ 服务就绪!")


# ============ 基础接口 ============

@app.get("/")
def root():
    """首页"""
    return {
        "name": "Bio-Agent",
        "description": "采访到叙事长文生成系统",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    """健康检查"""
    return {"status": "ok"}


# ============ 项目管理接口 ============

@app.post("/projects", response_model=ProjectResponse)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    """创建新项目"""
    project = Project(name=data.name, description=data.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.get("/projects", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    """列出所有项目"""
    return db.query(Project).all()


@app.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: UUID, db: Session = Depends(get_db)):
    """获取项目详情"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@app.delete("/projects/{project_id}")
def delete_project(project_id: UUID, db: Session = Depends(get_db)):
    """删除项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(project)
    db.commit()
    return {"message": "删除成功"}


# ============ 音频上传接口 ============

@app.post("/projects/{project_id}/audio")
def upload_audio(project_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传音频文件"""
    # 检查项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查文件类型
    allowed = {".mp3", ".wav", ".m4a", ".flac"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型，仅支持: {allowed}")
    
    # 保存文件
    save_dir = UPLOAD_DIR / str(project_id)
    save_dir.mkdir(exist_ok=True)
    file_path = save_dir / file.filename
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # 保存记录
    audio = AudioFile(
        project_id=project_id,
        filename=file.filename,
        file_path=str(file_path)
    )
    db.add(audio)
    db.commit()
    
    return {"message": "上传成功", "filename": file.filename}


@app.get("/projects/{project_id}/audio")
def list_audio(project_id: UUID, db: Session = Depends(get_db)):
    """列出项目的音频文件"""
    files = db.query(AudioFile).filter(AudioFile.project_id == project_id).all()
    return [{"id": f.id, "filename": f.filename, "duration": f.duration} for f in files]


# ============ 对话接口 ============

@app.get("/projects/{project_id}/dialogue")
def get_dialogue(project_id: UUID, db: Session = Depends(get_db)):
    """获取项目的对话数据"""
    dialogue = db.query(Dialogue).filter(Dialogue.project_id == project_id).first()
    if not dialogue:
        raise HTTPException(status_code=404, detail="暂无对话数据")
    return dialogue.content


# ============ 蓝图接口 ============

@app.get("/projects/{project_id}/blueprint")
def get_blueprint(project_id: UUID, db: Session = Depends(get_db)):
    """获取项目的叙事蓝图"""
    blueprint = db.query(Blueprint).filter(Blueprint.project_id == project_id).order_by(Blueprint.version.desc()).first()
    if not blueprint:
        raise HTTPException(status_code=404, detail="暂无蓝图")
    return blueprint.content


# ============ 文章接口 ============

@app.get("/projects/{project_id}/article")
def get_article(project_id: UUID, db: Session = Depends(get_db)):
    """获取项目的文章"""
    article = db.query(Article).filter(Article.project_id == project_id).order_by(Article.version.desc()).first()
    if not article:
        raise HTTPException(status_code=404, detail="暂无文章")
    return {
        "id": article.id,
        "title": article.title,
        "content": article.content,
        "footnotes": article.footnotes,
        "word_count": article.word_count,
        "version": article.version
    }


@app.get("/projects/{project_id}/article/markdown", response_class=PlainTextResponse)
def get_article_markdown(project_id: UUID, db: Session = Depends(get_db)):
    """获取文章的 Markdown 原文"""
    article = db.query(Article).filter(Article.project_id == project_id).order_by(Article.version.desc()).first()
    if not article:
        raise HTTPException(status_code=404, detail="暂无文章")
    return article.content


# ============ 流程控制接口（Step 2 实现） ============

@app.post("/projects/{project_id}/transcribe")
def start_transcribe(project_id: UUID, db: Session = Depends(get_db)):
    """开始转录音频（触发 AudioProcessingAgent）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # TODO: Step 2 实现 - 调用 AudioProcessingAgent
    project.status = "TRANSCRIBING"
    project.current_agent = "AudioProcessingAgent"
    db.commit()
    
    return {"message": "转录已开始", "status": project.status}


@app.post("/projects/{project_id}/plan")
def start_planning(project_id: UUID, db: Session = Depends(get_db)):
    """开始规划（触发 PlanningAgent）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # TODO: Step 2 实现 - 调用 PlanningAgent
    project.status = "PLANNING"
    project.current_agent = "PlanningAgent"
    db.commit()
    
    return {"message": "规划已开始", "status": project.status}


@app.post("/projects/{project_id}/write")
def start_writing(project_id: UUID, db: Session = Depends(get_db)):
    """开始写作（触发 WritingAgent）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # TODO: Step 2 实现 - 调用 WritingAgent
    project.status = "WRITING"
    project.current_agent = "WritingAgent"
    db.commit()
    
    return {"message": "写作已开始", "status": project.status}


# ============ 主程序入口 ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
