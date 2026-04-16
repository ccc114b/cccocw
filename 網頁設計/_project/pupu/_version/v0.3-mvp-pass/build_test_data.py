import sqlite3
import json
import os

db_path = os.path.join(os.path.dirname(__file__), 'pupu.db')
json_path = os.path.join(os.path.dirname(__file__), '_data', 'users.json')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('''
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    name TEXT,
    gender TEXT,
    age INTEGER,
    location TEXT,
    data TEXT
  )
''')

cursor.execute('''
  CREATE TABLE IF NOT EXISTS friendships (
    user_id INTEGER,
    friend_id INTEGER,
    PRIMARY KEY (user_id, friend_id)
  )
''')

cursor.execute('''
  CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    content TEXT,
    is_repost INTEGER DEFAULT 0,
    repost_of_id INTEGER,
    created_at TEXT,
    likes TEXT,
    comments TEXT
  )
''')

cursor.execute('''
  CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    from_user_id INTEGER,
    to_user_id INTEGER,
    content TEXT,
    created_at TEXT,
    is_read INTEGER DEFAULT 0
  )
''')

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for user in data['users']:
    cursor.execute(
      'INSERT OR REPLACE INTO users (id, username, password, name, gender, age, location, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
      (user['id'], user['username'], '', user['name'], user['gender'], user['age'], user['location'], json.dumps(user['data'], ensure_ascii=False))
    )

for f in data['friendships']:
    cursor.execute(
      'INSERT OR REPLACE INTO friendships (user_id, friend_id) VALUES (?, ?)',
      (f['user_id'], f['friend_id'])
    )

posts_path = os.path.join(os.path.dirname(__file__), '_data', 'posts.json')
with open(posts_path, 'r', encoding='utf-8') as f:
    posts_data = json.load(f)

for post in posts_data['posts']:
    cursor.execute(
      'INSERT OR REPLACE INTO posts (id, user_id, content, is_repost, repost_of_id, created_at, likes, comments) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
      (post['id'], post['user_id'], post['content'], 
       1 if post.get('is_repost') else 0,
       post.get('repost_of_id'),
       post['created_at'], 
       json.dumps(post.get('likes', []), ensure_ascii=False),
       json.dumps(post.get('comments', []), ensure_ascii=False))
    )

conn.commit()
print(f"Imported {len(data['users'])} users, {len(data['friendships'])} friendships, {len(posts_data['posts'])} posts")
conn.close()