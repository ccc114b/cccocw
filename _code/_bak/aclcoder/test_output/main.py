from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from contextlib import contextmanager

app = FastAPI(title="Blog API")

# 数据库配置
DATABASE = "blog.db"

# 数据库连接管理器
@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# 初始化数据库表
def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                author TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# 数据模型
class Post(BaseModel):
    id: Optional[int] = None
    title: str
    content: str
    author: str
    created_at: Optional[str] = None

class PostCreate(BaseModel):
    title: str
    content: str
    author: str

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None

# 初始化数据库
init_db()

# ===== API 端点 =====

# 获取所有文章
@app.get("/posts", response_model=List[Post])
def get_posts():
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM posts ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

# 获取单篇文章
@app.get("/posts/{post_id}", response_model=Post)
def get_post(post_id: int):
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="文章不存在")
        return dict(row)

# 创建文章
@app.post("/posts", response_model=Post)
def create_post(post: PostCreate):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO posts (title, content, author) VALUES (?, ?, ?)",
            (post.title, post.content, post.author)
        )
        conn.commit()
        post_id = cursor.lastrowid
        
        # 获取刚创建的文章
        cursor = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        row = cursor.fetchone()
        return dict(row)

# 更新文章
@app.put("/posts/{post_id}", response_model=Post)
def update_post(post_id: int, post: PostUpdate):
    with get_db() as conn:
        # 检查文章是否存在
        cursor = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 构建更新语句
        update_fields = []
        update_values = []
        
        if post.title is not None:
            update_fields.append("title = ?")
            update_values.append(post.title)
        if post.content is not None:
            update_fields.append("content = ?")
            update_values.append(post.content)
        if post.author is not None:
            update_fields.append("author = ?")
            update_values.append(post.author)
        
        if update_fields:
            update_values.append(post_id)
            conn.execute(
                f"UPDATE posts SET {', '.join(update_fields)} WHERE id = ?",
                update_values
            )
            conn.commit()
        
        # 获取更新后的文章
        cursor = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        row = cursor.fetchone()
        return dict(row)

# 删除文章
@app.delete("/posts/{post_id}")
def delete_post(post_id: int):
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
    
    return {"message": "文章刪除成功"}

# 根路径
@app.get("/")
def root():
    return {"message": "Blog API is running", "docs": "/docs"}