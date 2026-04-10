import { ApolloClient, InMemoryCache, HttpLink, gql } from '@apollo/client/core';
import { ApolloProvider, useQuery } from '@apollo/client/react';
import { BrowserRouter, Routes, Route, Link, useParams } from 'react-router-dom';
import './index.css';

const httpLink = new HttpLink({
  uri: 'http://localhost:8000/graphql',
});

const client = new ApolloClient({
  link: httpLink,
  cache: new InMemoryCache(),
});

const FEED_QUERY = gql`
  query Feed($limit: Int) {
    feed(limit: $limit) {
      id
      content
      createdAt
      likes
      author { id name }
    }
  }
`;

const POST_QUERY = gql`
  query Post($id: Int!) {
    post(id: $id) {
      id
      content
      createdAt
      likes
      commentsWithAuthors
      author { id name bio location }
    }
  }
`;

const USER_QUERY = gql`
  query User($id: Int!) {
    user(id: $id) {
      id
      name
      bio
      location
      age
      gender
      posts { id content createdAt likes }
    }
  }
`;

function formatTime(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now - date;
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (mins < 1) return 'now';
  if (mins < 60) return `${mins}m`;
  if (hours < 24) return `${hours}h`;
  if (days < 7) return `${days}d`;
  return date.toLocaleDateString();
}

function HeartIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#666" strokeWidth="2">
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
    </svg>
  );
}

function CommentIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#666" strokeWidth="2">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function BackIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M19 12H5M12 19l-7-7 7-7" />
    </svg>
  );
}

function PostCard({ post, onClick }) {
  return (
    <div className="post-card" onClick={onClick}>
      <div className="post-header">
        <div className="avatar">{post.author?.name?.charAt(0) || '?'}</div>
        <div className="post-meta">
          <span className="post-author">{post.author?.name || 'Unknown'}</span>
          <span className="post-time"> · {formatTime(post.createdAt)}</span>
        </div>
      </div>
      <div className="post-content">{post.content}</div>
      <div className="post-actions">
        <span className="action-btn"><HeartIcon /> {post.likes?.length || 0}</span>
      </div>
    </div>
  );
}

function Feed() {
  const { data, loading, error } = useQuery(FEED_QUERY, { variables: { limit: 20 } });
  if (loading) return <div className="loading">載入中...</div>;
  if (error) return <div className="error">錯誤: {error.message}</div>;

  return (
    <div>
      <div className="header"><h1>普普</h1></div>
      {data?.feed?.map(post => (
        <PostCard key={post.id} post={post} onClick={() => window.location.href = `/post/${post.id}`} />
      ))}
    </div>
  );
}

function parseComments(str) {
  try {
    if (!str || str === '[]' || str === '') return [];
    return JSON.parse(str);
  } catch { return []; }
}

function PostDetail() {
  const { id } = useParams();
  const postId = parseInt(id);
  const { data, loading, error } = useQuery(POST_QUERY, { variables: { id: postId } });

  if (loading) return <div className="loading">載入中...</div>;
  if (error) return <div className="error">錯誤: {error.message}</div>;

  const post = data?.post;
  if (!post) return <div className="error">貼文不存在</div>;

  const comments = parseComments(post.commentsWithAuthors);
  const likeCount = post.likes?.length || 0;
  const commentCount = comments.length || 0;

  return (
    <div>
      <div className="header"><Link to="/" className="back-btn"><BackIcon /> 返回</Link></div>
      <div className="post-card">
        <div className="post-header">
          <Link to={`/user/${post.author?.id}`} className="avatar">{post.author?.name?.charAt(0)}</Link>
          <div className="post-meta">
            <Link to={`/user/${post.author?.id}`} className="post-author">{post.author?.name}</Link>
            <span className="post-time"> · {formatTime(post.createdAt)}</span>
          </div>
        </div>
        <div className="post-content">{post.content}</div>
        <div className="post-actions">
          <span className="action-btn"><HeartIcon /> {likeCount}</span>
          <span className="action-btn"><CommentIcon /> {commentCount}</span>
        </div>
      </div>
      {commentCount > 0 && (
        <div className="comments-section">
          <div className="comments-title">{commentCount} 回覆</div>
          {comments.map((c, i) => (
            <div key={i} className="comment-item">
              <div className="comment-author">{c.author_name || `使用者 ${c.user_id}`}</div>
              <div className="comment-content">{c.content}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function UserProfile() {
  const { id } = useParams();
  const userId = parseInt(id);
  const { data, loading, error } = useQuery(USER_QUERY, { variables: { id: userId } });

  if (loading) return <div className="loading">載入中...</div>;
  if (error) return <div className="error">錯誤: {error.message}</div>;

  const user = data?.user;
  if (!user) return <div className="error">使用者不存在</div>;

  return (
    <div>
      <div className="header"><Link to="/" className="back-btn"><BackIcon /> 返回</Link></div>
      <div className="user-header">
        <div className="name">{user.name}</div>
        <div className="bio">{user.bio || '沒有簡介'}</div>
        <div className="info">{user.age} · {user.gender} · {user.location}</div>
      </div>
      {user.posts?.map(post => (
        <PostCard key={post.id} post={post} onClick={() => window.location.href = `/post/${post.id}`} />
      ))}
    </div>
  );
}

function App() {
  return (
    <ApolloProvider client={client}>
      <BrowserRouter>
        <div className="container">
          <Routes>
            <Route path="/" element={<Feed />} />
            <Route path="/post/:id" element={<PostDetail />} />
            <Route path="/user/:id" element={<UserProfile />} />
          </Routes>
        </div>
      </BrowserRouter>
    </ApolloProvider>
  );
}

export default App;