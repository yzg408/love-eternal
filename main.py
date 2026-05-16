#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""爱心永传 · 数字星火 - Backend API"""

import sqlite3
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB_PATH = Path(__file__).parent / "data" / "love_eternal.db"


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT '匿名星人',
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS capsules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icon TEXT NOT NULL DEFAULT '📝',
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL DEFAULT '匿名星人',
            created_at TEXT NOT NULL,
            is_public INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS chain_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emoji TEXT NOT NULL,
            name TEXT DEFAULT NULL,
            created_at TEXT NOT NULL
        );
    """)
    cur = conn.execute("SELECT COUNT(*) FROM capsules")
    if cur.fetchone()[0] == 0:
        default_caps = [
            ("📝", "写给未来的信", "给一年后、十年后、或者永远的自己\n写一封不会被遗忘的信", "数字星火", "2026-01-01 00:00"),
            ("🎵", "时光旋律", "记录此刻最触动你的一首歌、一段话\n让感动在数据中永恒", "数字星火", "2026-01-01 00:00"),
            ("🌱", "善举种子", "记下一件你做过的温暖小事\n它会像种子一样，在数字土壤里生长", "数字星火", "2026-01-01 00:00"),
            ("⭐", "星空心愿", "许下一个愿望，让它成为星空中\n最亮的那一颗", "数字星火", "2026-01-01 00:00"),
            ("💎", "数字遗产", "为你珍视的人留下一段话、一份记忆\n数字永生，爱永不消逝", "数字星火", "2026-01-01 00:00"),
            ("🌈", "爱心接力", "传递一份善意给下一个人\n让世界因为你的存在而更温暖", "数字星火", "2026-01-01 00:00"),
        ]
        conn.executemany(
            "INSERT INTO capsules (icon, title, content, author, created_at) VALUES (?,?,?,?,?)",
            default_caps
        )
    cur = conn.execute("SELECT COUNT(*) FROM chain_links")
    if cur.fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO chain_links (emoji, name, created_at) VALUES (?,?,?)",
            [("🤍", None, "2026-05-16 08:00"), ("💗", None, "2026-05-16 08:01"), ("❤️", None, "2026-05-16 08:02")]
        )
    conn.commit()
    conn.close()


class MessageCreate(BaseModel):
    name: str = Field(default="匿名星人", max_length=20)
    text: str = Field(..., max_length=200, min_length=1)


class CapsuleCreate(BaseModel):
    icon: str = Field(default="📝")
    title: str = Field(..., max_length=50)
    content: str = Field(..., max_length=500)
    author: str = Field(default="匿名星人", max_length=20)


class ChainCreate(BaseModel):
    name: str | None = Field(default=None, max_length=20)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="爱心永传 · 数字星火 API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/messages")
def list_messages():
    conn = get_db()
    rows = conn.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/messages")
def create_message(msg: MessageCreate):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO messages (name, text, created_at) VALUES (?,?,?)",
        (msg.name.strip() or "匿名星人", msg.text.strip(), now)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM messages WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.delete("/api/messages/{msg_id}")
def delete_message(msg_id: int):
    conn = get_db()
    cur = conn.execute("DELETE FROM messages WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(404, "留言不存在")
    return {"ok": True}


@app.get("/api/capsules")
def list_capsules():
    conn = get_db()
    rows = conn.execute("SELECT * FROM capsules WHERE is_public=1 ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/capsules/{capsule_id}")
def get_capsule(capsule_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM capsules WHERE id=?", (capsule_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "胶囊不存在")
    return dict(row)


@app.post("/api/capsules")
def create_capsule(cap: CapsuleCreate):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO capsules (icon, title, content, author, created_at) VALUES (?,?,?,?,?)",
        (cap.icon, cap.title.strip(), cap.content.strip(), cap.author.strip() or "匿名星人", now)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM capsules WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.get("/api/chain")
def get_chain():
    conn = get_db()
    rows = conn.execute("SELECT * FROM chain_links ORDER BY id ASC").fetchall()
    count = conn.execute("SELECT COUNT(*) FROM chain_links").fetchone()[0]
    conn.close()
    return {"count": count, "links": [dict(r) for r in rows]}


@app.post("/api/chain")
def add_chain_link(link: ChainCreate):
    import random
    emojis = ["💕", "💗", "💖", "✨", "🌟", "💫", "❤️", "💜", "🩷", "🌸", "🌺", "⭐", "🌙", "☀️"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO chain_links (emoji, name, created_at) VALUES (?,?,?)",
        (random.choice(emojis), link.name, now)
    )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM chain_links").fetchone()[0]
    conn.close()
    return {"count": count, "id": cur.lastrowid}


static_dir = Path(__file__).parent
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5188, reload=False)
