import sqlite3
import json
import os
from datetime import datetime
from typing import Optional
from functools import wraps

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette_graphene3 import GraphQLApp
import graphene
import bcrypt

DB_PATH = os.path.join(os.path.dirname(__file__), "pupu.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def open_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def dict_from_row(row):
    if row is None:
        return None
    return dict(row)


# ============ Models ============


class User(graphene.ObjectType):
    id = graphene.Int()
    username = graphene.String()
    name = graphene.String()
    gender = graphene.String()
    age = graphene.Int()
    location = graphene.String()
    bio = graphene.String()
    data = graphene.String()

    friends = graphene.List(lambda: User)
    posts = graphene.List(lambda: Post)

    def resolve_data(self, info):
        return self.data

    def resolve_friends(self, info):
        conn = open_db()
        cursor = conn.execute(
            "SELECT u.* FROM users u JOIN friendships f ON u.id = f.friend_id WHERE f.user_id = ?",
            (self.id,),
        )
        return [User(**dict_from_row(r)) for r in cursor.fetchall()]

    def resolve_posts(self, info):
        conn = open_db()
        cursor = conn.execute(
            "SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
            (self.id,),
        )
        rows = cursor.fetchall()
        return [
            Post(
                id=r["id"],
                user_id=r["user_id"],
                content=r["content"],
                is_repost=bool(r["is_repost"]),
                repost_of_id=r["repost_of_id"],
                created_at=r["created_at"],
                likes=r["likes"],
                comments_json=r["comments"],
            )
            for r in rows
        ]


class Post(graphene.ObjectType):
    id = graphene.Int()
    user_id = graphene.Int()
    content = graphene.String()
    is_repost = graphene.Boolean()
    repost_of_id = graphene.Int()
    created_at = graphene.String()
    likes = graphene.List(graphene.Int)
    comments_json = graphene.String()
    comments_with_authors = graphene.String()

    def resolve_comments_with_authors(self, info):
        import json

        comments = json.loads(self.comments_json) if self.comments_json else []
        if not comments:
            return []

        conn = open_db()
        user_ids = [c["user_id"] for c in comments if "user_id" in c]
        if not user_ids:
            return comments

        placeholders = ",".join(["?"] * len(user_ids))
        cursor = conn.execute(
            f"SELECT id, name FROM users WHERE id IN ({placeholders})", user_ids
        )
        users = {row["id"]: row["name"] for row in cursor.fetchall()}

        enriched = []
        for c in comments:
            c = dict(c)
            c["author_name"] = (
                users.get(c.get("user_id")) or f"使用者{c.get('user_id')}"
            )
            enriched.append(c)
        return json.dumps(enriched)

    author = graphene.Field(User)

    def resolve_author(self, info):
        conn = open_db()
        cursor = conn.execute(
            "SELECT id, username, name, gender, age, location, data FROM users WHERE id = ?",
            (self.user_id,),
        )
        row = cursor.fetchone()
        return User(**dict_from_row(row)) if row else None

    def resolve_likes(self, info):
        if isinstance(self.likes, list):
            return self.likes
        return json.loads(self.likes) if self.likes else []

    def resolve_comments(self, info):
        if isinstance(self.comments, list):
            return self.comments
        return json.loads(self.comments) if self.comments else []


class Message(graphene.ObjectType):
    id = graphene.Int()
    from_user_id = graphene.Int()
    to_user_id = graphene.Int()
    content = graphene.String()
    created_at = graphene.String()
    is_read = graphene.Boolean()

    from_user = graphene.Field(User)
    to_user = graphene.Field(User)

    def resolve_from_user(self, info):
        conn = open_db()
        cursor = conn.execute(
            "SELECT id, username, name, gender, age, location, data FROM users WHERE id = ?",
            (self.from_user_id,),
        )
        row = cursor.fetchone()
        return User(**dict_from_row(row)) if row else None

    def resolve_to_user(self, info):
        conn = open_db()
        cursor = conn.execute(
            "SELECT id, username, name, gender, age, location, data FROM users WHERE id = ?",
            (self.to_user_id,),
        )
        row = cursor.fetchone()
        return User(**dict_from_row(row)) if row else None


# ============ Queries ============


class Query(graphene.ObjectType):
    me = graphene.Field(User)
    user = graphene.Field(User, id=graphene.Int(), username=graphene.String())
    users = graphene.List(
        User, limit=graphene.Int(default_value=20), offset=graphene.Int(default_value=0)
    )
    feed = graphene.List(
        Post, limit=graphene.Int(default_value=20), offset=graphene.Int(default_value=0)
    )
    post = graphene.Field(Post, id=graphene.Int())
    my_friends = graphene.List(User)
    messages = graphene.List(Message, user_id=graphene.Int())

    def resolve_me(self, info):
        user_id = info.context.get("user_id")
        if not user_id:
            return None
        conn = open_db()
        cursor = conn.execute(
            "SELECT id, username, name, gender, age, location, data FROM users WHERE id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        return User(**dict_from_row(row)) if row else None

    def resolve_user(self, info, id=None, username=None):
        conn = open_db()
        if id:
            cursor = conn.execute(
                "SELECT id, username, name, gender, age, location, data FROM users WHERE id = ?",
                (id,),
            )
        elif username:
            cursor = conn.execute(
                "SELECT id, username, name, gender, age, location, data FROM users WHERE username = ?",
                (username,),
            )
        else:
            return None
        row = cursor.fetchone()
        return User(**dict_from_row(row)) if row else None

    def resolve_users(self, info, limit=20, offset=0):
        conn = open_db()
        cursor = conn.execute(
            "SELECT id, username, name, gender, age, location, data FROM users LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [User(**dict_from_row(r)) for r in cursor.fetchall()]

    def resolve_feed(self, info, limit=20, offset=0):
        user_id = info.context.get("user_id")
        conn = open_db()
        if user_id:
            cursor = conn.execute(
                """
                SELECT p.* FROM posts p
                JOIN friendships f ON p.user_id = f.friend_id
                WHERE f.user_id = ? AND p.content != ''
                ORDER BY p.created_at DESC
                LIMIT ? OFFSET ?
            """,
                (user_id, limit, offset),
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM posts WHERE content != '' ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        rows = cursor.fetchall()
        return [
            Post(
                id=r["id"],
                user_id=r["user_id"],
                content=r["content"],
                is_repost=bool(r["is_repost"]),
                repost_of_id=r["repost_of_id"],
                created_at=r["created_at"],
                likes=r["likes"],
                comments_json=r["comments"],
            )
            for r in rows
        ]

    def resolve_post(self, info, id):
        conn = open_db()
        cursor = conn.execute("SELECT * FROM posts WHERE id = ?", (id,))
        row = cursor.fetchone()
        if not row:
            return None
        return Post(
            id=row["id"],
            user_id=row["user_id"],
            content=row["content"],
            is_repost=bool(row["is_repost"]),
            repost_of_id=row["repost_of_id"],
            created_at=row["created_at"],
            likes=row["likes"],
            comments_json=row["comments"],
        )

    def resolve_my_friends(self, info):
        user_id = info.context.get("user_id")
        if not user_id:
            return []
        conn = open_db()
        cursor = conn.execute(
            "SELECT u.* FROM users u JOIN friendships f ON u.id = f.friend_id WHERE f.user_id = ?",
            (user_id,),
        )
        return [User(**dict_from_row(r)) for r in cursor.fetchall()]

    def resolve_messages(self, info, user_id):
        my_id = info.context.get("user_id")
        if not my_id:
            return []
        conn = open_db()
        cursor = conn.execute(
            """
            SELECT * FROM messages 
            WHERE (from_user_id = ? AND to_user_id = ?) OR (from_user_id = ? AND to_user_id = ?)
            ORDER BY created_at DESC
        """,
            (my_id, user_id, user_id, my_id),
        )
        return [Message(**dict_from_row(r)) for r in cursor.fetchall()]


# ============ Mutations ============


class Register(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        name = graphene.String(required=True)
        gender = graphene.String(required=True)
        age = graphene.Int(required=True)
        location = graphene.String(required=True)

    success = graphene.Boolean()
    user = graphene.Field(User)
    token = graphene.String()

    def mutate(self, info, username, password, name, gender, age, location):
        conn = open_db()
        cursor = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            raise Exception("Username already exists")

        cursor = conn.execute(
            "INSERT INTO users (username, password, name, gender, age, location, data) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                username,
                bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode("ascii"),
                name,
                gender,
                age,
                location,
                json.dumps({"bio": "", "interests": [], "preferences": {}}),
            ),
        )
        conn.commit()

        cursor = conn.execute(
            "SELECT id, username, name, gender, age, location, data FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        user = User(**dict_from_row(row))

        token = f"token_{user.id}_{datetime.now().timestamp()}"

        return Register(success=True, user=user, token=token)


class Login(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    success = graphene.Boolean()
    user = graphene.Field(User)
    token = graphene.String()

    def mutate(self, info, username, password):
        conn = open_db()
        cursor = conn.execute(
            "SELECT id, username, name, gender, age, location, data FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if not row or not bcrypt.checkpw(
            password.encode()[:72], row["password"].encode("ascii")
        ):
            raise Exception("Invalid username or password")

        user = User(**dict_from_row(row))
        token = f"token_{user.id}_{datetime.now().timestamp()}"

        return Login(success=True, user=user, token=token)


class CreatePost(graphene.Mutation):
    class Arguments:
        content = graphene.String(required=True)
        repost_of_id = graphene.Int()

    success = graphene.Boolean()
    post = graphene.Field(Post)

    def mutate(self, info, content, repost_of_id=None):
        user_id = info.context.get("user_id")
        if not user_id:
            raise Exception("Not authenticated")

        conn = open_db()
        cursor = conn.execute(
            "INSERT INTO posts (user_id, content, is_repost, repost_of_id, created_at, likes, comments) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                content,
                bool(repost_of_id),
                repost_of_id,
                datetime.now().isoformat(),
                "[]",
                "[]",
            ),
        )
        conn.commit()

        cursor = conn.execute("SELECT * FROM posts WHERE id = ?", (cursor.lastrowid,))
        row = cursor.fetchone()
        return CreatePost(
            success=True,
            post=Post(
                id=row["id"],
                user_id=row["user_id"],
                content=row["content"],
                is_repost=bool(row["is_repost"]),
                repost_of_id=row["repost_of_id"],
                created_at=row["created_at"],
                likes=row["likes"],
                comments_json=row["comments"],
            ),
        )


class AddComment(graphene.Mutation):
    class Arguments:
        post_id = graphene.Int(required=True)
        content = graphene.String(required=True)

    success = graphene.Boolean()

    def mutate(self, info, post_id, content):
        user_id = info.context.get("user_id")
        if not user_id:
            raise Exception("Not authenticated")

        conn = open_db()
        cursor = conn.execute("SELECT comments FROM posts WHERE id = ?", (post_id,))
        row = cursor.fetchone()
        if not row:
            raise Exception("Post not found")

        comments = json.loads(row["comments"]) if row["comments"] else []
        comments.append(
            {
                "user_id": user_id,
                "content": content,
                "created_at": datetime.now().isoformat(),
            }
        )

        conn.execute(
            "UPDATE posts SET comments = ? WHERE id = ?",
            (json.dumps(comments, ensure_ascii=False), post_id),
        )
        conn.commit()

        return AddComment(success=True)


class ToggleLike(graphene.Mutation):
    class Arguments:
        post_id = graphene.Int(required=True)

    success = graphene.Boolean()

    def mutate(self, info, post_id):
        user_id = info.context.get("user_id")
        if not user_id:
            raise Exception("Not authenticated")

        conn = open_db()
        cursor = conn.execute("SELECT likes FROM posts WHERE id = ?", (post_id,))
        row = cursor.fetchone()
        if not row:
            raise Exception("Post not found")

        likes = json.loads(row["likes"]) if row["likes"] else []
        if user_id in likes:
            likes.remove(user_id)
        else:
            likes.append(user_id)

        conn.execute(
            "UPDATE posts SET likes = ? WHERE id = ?", (json.dumps(likes), post_id)
        )
        conn.commit()

        return ToggleLike(success=True)


class AddFriend(graphene.Mutation):
    class Arguments:
        user_id = graphene.Int(required=True)

    success = graphene.Boolean()

    def mutate(self, info, user_id):
        my_id = info.context.get("user_id")
        if not my_id:
            raise Exception("Not authenticated")
        if my_id == user_id:
            raise Exception("Cannot add yourself")

        conn = open_db()
        try:
            conn.execute(
                "INSERT INTO friendships (user_id, friend_id) VALUES (?, ?)",
                (my_id, user_id),
            )
            conn.commit()
        except:
            pass

        return AddFriend(success=True)


class SendMessage(graphene.Mutation):
    class Arguments:
        to_user_id = graphene.Int(required=True)
        content = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.Field(Message)

    def mutate(self, info, to_user_id, content):
        user_id = info.context.get("user_id")
        if not user_id:
            raise Exception("Not authenticated")

        conn = open_db()
        cursor = conn.execute(
            "INSERT INTO messages (from_user_id, to_user_id, content, created_at, is_read) VALUES (?, ?, ?, ?, ?)",
            (user_id, to_user_id, content, datetime.now().isoformat(), 0),
        )
        conn.commit()

        cursor = conn.execute(
            "SELECT * FROM messages WHERE id = ?", (cursor.lastrowid,)
        )
        row = cursor.fetchone()
        return SendMessage(success=True, message=Message(**dict_from_row(row)))


class Mutation(graphene.ObjectType):
    register = Register.Field()
    login = Login.Field()
    create_post = CreatePost.Field()
    add_comment = AddComment.Field()
    toggle_like = ToggleLike.Field()
    add_friend = AddFriend.Field()
    send_message = SendMessage.Field()


# ============ App Setup ============

schema = graphene.Schema(query=Query, mutation=Mutation)

app = FastAPI(title="Pupu API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication middleware
@app.middleware("http")
async def auth_middleware(request, call_next):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token.startswith("token_"):
        parts = token.split("_")
        if len(parts) >= 2:
            request.state.user_id = int(parts[1])
    else:
        request.state.user_id = None

    response = await call_next(request)
    return response


# Context for GraphQL
def get_graphql_context(request):
    return {"request": request, "user_id": getattr(request.state, "user_id", None)}


app.add_route("/graphql", GraphQLApp(schema=schema, context_value=get_graphql_context))
app.add_route("/graphiql", GraphQLApp(schema=schema, playground=True))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
