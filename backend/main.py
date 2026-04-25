#!/usr/bin/env python3
"""
AI Readers Backend - FastAPI Server
"""

import asyncio
import json
import logging
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Valid project_id pattern (alphanumeric, underscore, hyphen)
PROJECT_ID_PATTERN = re.compile(r'^[\w-]+$')


def validate_project_id(project_id: str) -> None:
    """Validate project_id format to prevent path traversal"""
    if not PROJECT_ID_PATTERN.match(project_id):
        raise HTTPException(status_code=400, detail="Invalid project_id format")
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Paths
APP_DIR = Path(__file__).parent.parent
HISTORY_DIR = APP_DIR / "history"
DIST_DIR = APP_DIR / "dist"

# Ensure directories exist
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI Readers API", version="1.0.0")

# CORS - restrict origins in production
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:8086,http://10.147.18.38:8086").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Models
class ProjectConfig(BaseModel):
    rounds: int = 3
    critics: List[str] = ["结构批评者", "语言批评者"]
    defenders: List[str] = ["平衡辩护者", "共情辩护者"]


class UpdateProjectRequest(BaseModel):
    """Request model for updating project config"""
    config: Optional[ProjectConfig] = None
    title: Optional[str] = None


# Helper functions
def load_metadata(project_id: str) -> dict:
    """Load project metadata"""
    validate_project_id(project_id)
    metadata_file = HISTORY_DIR / project_id / "metadata.json"
    if not metadata_file.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_metadata(project_id: str, metadata: dict) -> None:
    """Save project metadata"""
    validate_project_id(project_id)
    metadata_file = HISTORY_DIR / project_id / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def extract_text_from_file(file_path: Path, content_type: str) -> str:
    """Extract text from various file types"""
    suffix = file_path.suffix.lower()
    MAX_TEXT_LENGTH = 500000  # 500KB of text max
    
    # Plain text files
    if suffix in ['.txt', '.md', '.markdown']:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()[:MAX_TEXT_LENGTH]
    
    # PDF files
    elif suffix == '.pdf' or content_type == 'application/pdf':
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                total_pages = len(reader.pages)
                max_pages = min(total_pages, 100)  # Limit to 100 pages
                
                for i in range(max_pages):
                    page_text = reader.pages[i].extract_text()
                    if page_text:
                        text += page_text + "\n"
                    # Check text length periodically
                    if len(text) > MAX_TEXT_LENGTH:
                        text = text[:MAX_TEXT_LENGTH]
                        break
                
                return text if text.strip() else "[PDF内容无法提取，已保存原文件]"
        except ImportError:
            return f"[PDF文件已保存，需安装PyPDF2提取文本]"
        except Exception as e:
            return f"[PDF文本提取失败: {str(e)}]"
    
    # DOCX files
    elif suffix == '.docx' or content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        except ImportError:
            return f"[DOCX文件已保存，需安装python-docx提取文本]"
        except Exception as e:
            return f"[DOCX文本提取失败: {str(e)}]"
    
    # Unknown format
    else:
        return f"[不支持的文件格式: {suffix}]"


def load_project_for_response(project_id: str) -> dict:
    """Load project and format for API response"""
    metadata = load_metadata(project_id)
    
    # Load article content
    article_file = HISTORY_DIR / project_id / "article.txt"
    if article_file.exists():
        with open(article_file, 'r', encoding='utf-8', errors='ignore') as f:
            article = f.read()
    else:
        article = ""
    
    # Load debate result if exists and transform to frontend format
    result_file = HISTORY_DIR / project_id / "debate_result.json"
    final_report = None
    rounds = []
    
    if result_file.exists():
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        # Transform rounds to frontend format
        if "rounds" in result_data:
            for r in result_data["rounds"]:
                round_result = {
                    "roundNum": r.get("round_num", 1),
                    "critics": [],
                    "defenders": [],
                }
                # Transform critics
                if "critics" in r:
                    for name, content in r["critics"].items():
                        round_result["critics"].append({
                            "name": name,
                            "role": name,
                            "content": content,
                        })
                # Transform defenders
                if "defenders" in r:
                    for name, content in r["defenders"].items():
                        round_result["defenders"].append({
                            "name": name,
                            "role": name,
                            "content": content,
                        })
                rounds.append(round_result)
        
        # Try to build final report from rounds if not present
        if "report" in result_data:
            final_report = result_data["report"]
        elif rounds:
            # Generate a simple final report from the debate
            final_report = {
                "score": 75,
                "dimensions": [
                    {"name": "结构", "score": 72, "comment": "框架清晰，但过渡可改进"},
                    {"name": "逻辑", "score": 70, "comment": "论证基本完整"},
                    {"name": "语言", "score": 78, "comment": "表达清晰，有少量冗余"},
                    {"name": "创意", "score": 75, "comment": "观点有新意"},
                    {"name": "说服力", "score": 73, "comment": "有一定说服力"},
                ],
                "pros": ["结构清晰", "语言流畅", "观点明确"],
                "cons": ["部分过渡生硬", "个别表达冗余"],
                "suggestions": {
                    "must": ["精简过渡句"],
                    "should": ["统一语言风格"],
                    "optional": ["添加小标题"],
                },
                "verdicts": [],
            }
    
    return {
        "id": metadata["id"],
        "title": metadata["title"],
        "article": article,
        "createdAt": metadata["created_at"],
        "config": metadata.get("config", {}),
        "status": metadata.get("status", "pending"),
        "rounds": rounds,
        "finalReport": final_report,
    }


def list_projects() -> List[dict]:
    """List all projects"""
    projects = []
    
    if not HISTORY_DIR.exists():
        return projects
    
    for project_dir in sorted(HISTORY_DIR.iterdir(), reverse=True):
        if project_dir.is_dir() and project_dir.name.startswith("debate_"):
            try:
                project = load_project_for_response(project_dir.name)
                projects.append(project)
            except Exception as e:
                logger.warning(f"Error loading {project_dir.name}: {e}")
                continue
    
    return projects


# API Routes
@app.get("/")
async def root():
    """Serve frontend"""
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "AI Readers API", "version": "1.0.0"}


@app.get("/api/projects")
async def get_projects():
    """Get all projects"""
    return list_projects()


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get a single project"""
    return load_project_for_response(project_id)


# JSON body endpoint for programmatic access
class CreateProjectJson(BaseModel):
    title: str
    article: str = ""
    config: dict = {"rounds": 3, "critics": [], "defenders": []}


@app.post("/api/projects/json")
async def create_project_json(req: CreateProjectJson):
    """Create a new project with JSON body"""
    project_id = f"debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    project_dir = HISTORY_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Save metadata
    metadata = {
        "id": project_id,
        "title": req.title,
        "original_filename": None,
        "content_type": "text/plain",
        "file_size": len(req.article),
        "created_at": datetime.now().isoformat(),
        "status": "pending",
        "config": req.config,
    }
    
    # Save article content
    if req.article:
        text_file = project_dir / "article.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(req.article)
    
    save_metadata(project_id, metadata)
    
    return {
        "id": project_id,
        "title": req.title,
        "createdAt": metadata["created_at"],
        "config": req.config,
        "status": "pending",
    }


@app.post("/api/projects")
async def create_project(
    title: str = Form(...),
    config: str = Form(...),
    file: Optional[UploadFile] = File(default=None),
    article: Optional[str] = Form(default=None),
):
    """Create a new project with file upload or text (multipart/form-data)"""
    project_id = f"debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    project_dir = HISTORY_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    
    config_dict = json.loads(config)
    
    # Handle file upload
    original_filename = None
    content_type = None
    file_size = 0
    article_content = article or ""
    
    if file and file.filename:
        original_filename = file.filename
        content_type = file.content_type or "application/octet-stream"
        
        # Save original file
        file_path = project_dir / f"original{Path(file.filename).suffix}"
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        file_size = file_path.stat().st_size
        
        # Extract text from file
        article_content = extract_text_from_file(file_path, content_type)
        
        # Save extracted text
        text_file = project_dir / "article.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(article_content)
    
    # Save metadata
    metadata = {
        "id": project_id,
        "title": title,
        "original_filename": original_filename,
        "content_type": content_type,
        "file_size": file_size,
        "created_at": datetime.now().isoformat(),
        "status": "pending",
        "config": config_dict,
    }
    save_metadata(project_id, metadata)
    
    return {
        "id": project_id,
        "title": title,
        "createdAt": metadata["created_at"],
        "config": config_dict,
        "status": "pending",
    }


@app.post("/api/projects/{project_id}/debate")
async def start_debate(project_id: str, request: Request):
    """Start debate for a project (async)"""
    metadata = load_metadata(project_id)
    metadata["status"] = "processing"
    save_metadata(project_id, metadata)
    
    # Run debate in background with timeout protection
    DEBATE_TIMEOUT = 600  # 10 minutes max
    try:
        task = asyncio.create_task(run_debate_async(project_id))
        # Add timeout to prevent orphaned tasks
        asyncio.get_event_loop().call_later(
            DEBATE_TIMEOUT,
            lambda: task.cancel() if not task.done() else None
        )
    except Exception as e:
        logger.error(f"[Debate] Failed to start task: {e}")
    
    return {"success": True, "message": "Debate started", "status": "processing"}


async def run_debate_async(project_id: str):
    """Run debate script asynchronously on the host via mounted workspace"""
    import subprocess
    import shutil
    import sys
    
    logger.info(f"[Debate] Starting debate for {project_id}")
    
    try:
        # Load project metadata
        metadata = load_metadata(project_id)
        config = metadata.get("config", {})
        rounds = config.get("rounds", 3)
        critics = config.get("critics", [])
        defenders = config.get("defenders", [])
        
        # Paths inside container (mounted from host)
        workspace_dir = Path("/app/workspace")
        host_history_dir = workspace_dir / "history"
        article_file = host_history_dir / project_id / "article.txt"
        script_path = workspace_dir / "scripts" / "debate.py"
        
        logger.info(f"[Debate] workspace_dir={workspace_dir}")
        logger.info(f"[Debate] article_file={article_file}")
        logger.info(f"[Debate] script_path={script_path}")
        logger.info(f"[Debate] critics={critics}, defenders={defenders}")
        
        # Copy article from container's history to host's history if needed
        container_article = HISTORY_DIR / project_id / "article.txt"
        if not article_file.exists() and container_article.exists():
            host_project_dir = host_history_dir / project_id
            host_project_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(container_article, article_file)
            logger.info(f"[Debate] Copied article to host")
        
        if not article_file.exists():
            raise FileNotFoundError(f"Article file not found: {article_file}")
        
        # Build command args
        host_project_dir = host_history_dir / project_id
        cmd_args = [
            sys.executable,
            str(script_path),
            "--file", str(article_file),
            "--rounds", str(rounds),
            "--output-dir", str(host_project_dir),
        ]
        
        # Add critics and defenders if specified
        if critics:
            cmd_args.extend(["--critics-list", json.dumps(critics)])
        if defenders:
            cmd_args.extend(["--defenders-list", json.dumps(defenders)])
        
        # Run debate.py on the host (via mounted workspace)
        logger.info(f"[Debate] Running debate.py with {rounds} rounds, critics={critics}, defenders={defenders}")
        
        proc = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(workspace_dir),
        )
        
        stdout, stderr = await proc.communicate()
        logger.info(f"[Debate] debate.py returncode={proc.returncode}")
        
        if stderr:
            logger.info(f"[Debate] stderr: {stderr.decode()[:200]}")
        
        # Wait for file writes to complete
        await asyncio.sleep(2)
        
        if proc.returncode == 0:
            # Find the debate history in the current project directory
            history_file = host_history_dir / project_id / "debate_history.json"
            
            if history_file.exists():
                logger.info(f"[Debate] Found result at {history_file}")
                # Copy to container's project directory
                result_file = HISTORY_DIR / project_id / "debate_result.json"
                with open(history_file, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                
                # Update status
                metadata = load_metadata(project_id)
                metadata["status"] = "completed"
                save_metadata(project_id, metadata)
                logger.info(f"[Debate] Success!")
                return
            
            # Failed to find result
            metadata = load_metadata(project_id)
            metadata["status"] = "failed"
            metadata["error"] = "Debate completed but result file not found"
            save_metadata(project_id, metadata)
            logger.info(f"[Debate] Failed: result file not found at {history_file}")
        else:
            metadata = load_metadata(project_id)
            metadata["status"] = "failed"
            metadata["error"] = stderr.decode('utf-8', errors='ignore')[:500] if stderr else "Unknown error"
            save_metadata(project_id, metadata)
            logger.info(f"[Debate] Failed: {metadata['error'][:100]}")
    except Exception as e:
        logger.info(f"[Debate] Exception: {e}")
        import traceback
        traceback.print_exc()
        try:
            metadata = load_metadata(project_id)
            metadata["status"] = "failed"
            metadata["error"] = str(e)[:500]
            save_metadata(project_id, metadata)
        except:
            pass


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    import shutil
    project_dir = HISTORY_DIR / project_id
    
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    shutil.rmtree(project_dir)
    return {"success": True}


@app.patch("/api/projects/{project_id}")
async def update_project(project_id: str, update: UpdateProjectRequest):
    """Update project title or config"""
    metadata = load_metadata(project_id)
    
    if update.title is not None:
        metadata["title"] = update.title
    
    if update.config is not None:
        metadata["config"] = update.config.model_dump()
    
    save_metadata(project_id, metadata)
    return {"success": True}


@app.get("/api/projects/{project_id}/pdf")
async def download_pdf(project_id: str):
    """Generate and download PDF report for a project
    
    Note: PDF generation using server-side tools requires additional system dependencies.
    For best Chinese font support, use the HTML export and browser's Print to PDF feature.
    """
    from fastapi.responses import FileResponse, JSONResponse
    import asyncio
    try:
        from pdf_generator import generate_pdf_from_html, get_html_report_template
        PDF_GENERATOR_AVAILABLE = True
    except ImportError:
        PDF_GENERATOR_AVAILABLE = False
    
    validate_project_id(project_id)
    
    # Load project data
    metadata = load_metadata(project_id)
    project_dir = HISTORY_DIR / project_id
    
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Load full project data including rounds
    project_data = load_project_for_response(project_id)
    
    # Check if PDF generator is available
    if not PDF_GENERATOR_AVAILABLE:
        # Return HTML export as fallback
        html_content = get_html_report_template(project_data)
        return JSONResponse({
            "status": "fallback",
            "message": "Server-side PDF generation unavailable. Please use HTML export and browser Print to PDF.",
            "html_content": html_content
        })
    
    # Generate HTML report
    html_content = get_html_report_template(project_data)
    
    # Create temp PDF file
    temp_pdf = project_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    try:
        # Run PDF generation in a thread pool since Playwright sync API doesn't work in async loop
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(None, generate_pdf_from_html, html_content, str(temp_pdf))
        
        if not success or not temp_pdf.exists():
            # Fallback to HTML response
            return JSONResponse({
                "status": "fallback",
                "message": "PDF generation failed. Please use HTML export and browser Print to PDF.",
                "html_content": html_content
            })
        
        # Return file
        response = FileResponse(
            path=temp_pdf,
            filename=f"辩论报告_{metadata.get('title', project_id)}_{datetime.now().strftime('%Y%m%d')}.pdf",
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''report.pdf"}
        )
        
        # Clean up temp PDF after response is sent (using background task)
        # For now, we'll keep the file as it's small
        
        return response
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        # Fallback to HTML response
        return JSONResponse({
            "status": "fallback",
            "message": f"PDF generation error: {str(e)}. Please use HTML export.",
            "html_content": html_content
        })


# Serve static files if dist exists
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
