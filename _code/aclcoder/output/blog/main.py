from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

# 資料庫設定
DATABASE_URL = "sqlite:///blog.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 資料庫模型
class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    content = Column(Text)

Base.metadata.create_all(bind=engine)

# Pydantic 模型
class PostCreate(BaseModel):
    title: str
    content: str

class PostResponse(BaseModel):
    id: int
    title: str
    content: str

# FastAPI 應用
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 獲取資料庫會話
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 首頁 - 文章列表
@app.get("/", response_class=HTMLResponse)
async def read_posts(request: Request, db: Session = None):
    if db is None:
        db = SessionLocal()
    posts = db.query(Post).all()
    return templates.TemplateResponse("index.html", {"request": request, "posts": posts})

# 顯示單篇文章
@app.get("/post/{post_id}", response_class=HTMLResponse)
async def read_post(request: Request, post_id: int, db: Session = None):
    if db is None:
        db = SessionLocal()
    post = db.query(Post).filter(Post.id == post_id).first()
    return templates.TemplateResponse("post.html", {"request": request, "post": post})

# 建立文章頁面
@app.get("/create", response_class=HTMLResponse)
async def create_page(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})

# 建立文章 API
@app.post("/posts")
async def create_post(post: PostCreate):
    db = SessionLocal()
    db_post = Post(title=post.title, content=post.content)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    db.close()
    return {"message": "文章建立成功", "id": db_post.id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)