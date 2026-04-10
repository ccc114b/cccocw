import { useState } from 'react';
import { ApolloClient, InMemoryCache, HttpLink, gql } from '@apollo/client/core';
import { ApolloProvider, useQuery, useMutation } from '@apollo/client/react';
import { BrowserRouter, Routes, Route, Link, useNavigate, useParams } from 'react-router-dom';
import './index.css';

const httpLink = new HttpLink({ uri: 'http://localhost:8000/graphql' });

const client = new ApolloClient({ link: httpLink, cache: new InMemoryCache() });

const FEED_QUERY = gql`
  query Feed($limit: Int) {
    feed(limit: $limit) {
      id content createdAt likes
      author { id name }
    }
  }
`;

const POST_QUERY = gql`
  query Post($id: Int!) {
    post(id: $id) {
      id content createdAt likes commentsWithAuthors
      author { id name bio location }
    }
  }
`;

const USER_QUERY = gql`
  query User($id: Int!) {
    user(id: $id) {
      id name bio location age gender
      posts { id content createdAt likes }
    }
  }
`;

const LOGIN_MUTATION = gql`
  mutation Login($username: String!, $password: String!) {
    login(username: $username, password: $password) {
      success token user { id name }
    }
  }
`;

const REGISTER_MUTATION = gql`
  mutation Register($username: String!, $password: String!, $name: String!, $gender: String!, $age: Int!, $location: String!) {
    register(username: $username, password: $password, name: $name, gender: $gender, age: $age, location: $location) {
      success token user { id name }
    }
  }
`;

const CREATE_POST_MUTATION = gql`
  mutation CreatePost($content: String!) {
    createPost(content: $content) {
      success post { id content }
    }
  }
`;

const ADD_COMMENT_MUTATION = gql`
  mutation AddComment($postId: Int!, $content: String!) {
    addComment(postId: $postId, content: $content) {
      success
    }
  }
`;

const TOGGLE_LIKE_MUTATION = gql`
  mutation ToggleLike($postId: Int!) {
    toggleLike(postId: $postId) {
      success
    }
  }
`;

function formatTime(dateStr) {
  const date = new Date(dateStr);
  const diff = new Date() - date;
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

function Feed({ user }) {
  const { data, loading, error, refetch } = useQuery(FEED_QUERY, { variables: { limit: 20 } });
  const [createPost] = useMutation(CREATE_POST_MUTATION);
  const [postText, setPostText] = useState('');
  const [posting, setPosting] = useState(false);

  if (loading) return <div className="loading">載入中...</div>;
  if (error) return <div className="error">錯誤: {error.message}</div>;

  const handlePost = async (e) => {
    e.preventDefault();
    if (!postText.trim() || !user) return;
    setPosting(true);
    try {
      await createPost({ variables: { content: postText } });
      setPostText('');
      refetch();
    } catch (err) {
      alert(err.message);
    }
    setPosting(false);
  };

  return (
    <div>
      <div className="header">
        <h1>普普</h1>
        {user ? (
          <Link to="/logout" className="nav-link">登出</Link>
        ) : (
          <Link to="/login" className="nav-link">登入</Link>
        )}
      </div>
      
      {user && (
        <form className="post-form" onSubmit={handlePost}>
          <textarea 
            placeholder="分享你的想法..." 
            value={postText}
            onChange={e => setPostText(e.target.value)}
            disabled={posting}
          />
          <button type="submit" disabled={posting || !postText.trim()}>
            {posting ? '發布中...' : '發布'}
          </button>
        </form>
      )}
      
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
  const { data, loading, error, refetch } = useQuery(POST_QUERY, { variables: { id: parseInt(id) } });
  const [addComment] = useMutation(ADD_COMMENT_MUTATION);
  const [toggleLike] = useMutation(TOGGLE_LIKE_MUTATION);
  const [commentText, setCommentText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const user = JSON.parse(localStorage.getItem('user') || 'null');

  if (loading) return <div className="loading">載入中...</div>;
  if (error) return <div className="error">錯誤: {error.message}</div>;

  const post = data?.post;
  if (!post) return <div className="error">貼文不存在</div>;

  const comments = parseComments(post.commentsWithAuthors);

  const handleComment = async (e) => {
    e.preventDefault();
    if (!commentText.trim() || !user) return;
    setSubmitting(true);
    try {
      await addComment({ variables: { postId: post.id, content: commentText } });
      setCommentText('');
      refetch();
    } catch (err) {
      alert(err.message);
    }
    setSubmitting(false);
  };

  const handleLike = async () => {
    if (!user) {
      alert('請先登入');
      return;
    }
    try {
      await toggleLike({ variables: { postId: post.id } });
      refetch();
    } catch (err) {
      alert(err.message);
    }
  };

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
          <button className="action-btn" onClick={handleLike}><HeartIcon /> {post.likes?.length || 0}</button>
          <span className="action-btn">{comments.length} 回覆</span>
        </div>
      </div>
      
      {user && (
        <form className="comment-form" onSubmit={handleComment}>
          <input 
            type="text" 
            placeholder="寫下你的回覆..." 
            value={commentText}
            onChange={e => setCommentText(e.target.value)}
            disabled={submitting}
          />
          <button type="submit" disabled={submitting || !commentText.trim()}>
            {submitting ? '傳送中...' : '回覆'}
          </button>
        </form>
      )}
      
      {comments.length > 0 && (
        <div className="comments-section">
          <div className="comments-title">{comments.length} 回覆</div>
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
  const { data, loading, error } = useQuery(USER_QUERY, { variables: { id: parseInt(id) } });
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

function LoginForm({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [gender, setGender] = useState('other');
  const [age, setAge] = useState(25);
  const [location, setLocation] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const [login] = useMutation(LOGIN_MUTATION);
  const [register] = useMutation(REGISTER_MUTATION);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = isRegister
        ? await register({ variables: { username, password, name, gender, age, location } })
        : await login({ variables: { username, password } });
      
      const data = result.data?.[isRegister ? 'register' : 'login'];
      if (data?.success) {
        localStorage.setItem('token', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        onLogin(data.user);
        navigate('/');
      } else {
        setError('登入失敗');
      }
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  return (
    <div className="auth-form">
      <div className="header"><Link to="/" className="back-btn"><BackIcon /> 返回</Link></div>
      <h2>{isRegister ? '註冊' : '登入'}</h2>
      <form onSubmit={handleSubmit}>
        <input type="text" placeholder="帳號" value={username} onChange={e => setUsername(e.target.value)} required />
        <input type="password" placeholder="密碼" value={password} onChange={e => setPassword(e.target.value)} required />
        
        {isRegister && (
          <>
            <input type="text" placeholder="顯示名稱" value={name} onChange={e => setName(e.target.value)} required />
            <select value={gender} onChange={e => setGender(e.target.value)}>
              <option value="male">男</option>
              <option value="female">女</option>
              <option value="other">其他</option>
            </select>
            <input type="number" placeholder="年齡" value={age} onChange={e => setAge(parseInt(e.target.value))} required />
            <input type="text" placeholder="地點" value={location} onChange={e => setLocation(e.target.value)} required />
          </>
        )}
        
        {error && <div className="error">{error}</div>}
        <button type="submit" disabled={loading}>{loading ? '處理中...' : (isRegister ? '註冊' : '登入')}</button>
      </form>
      <p className="switch-mode">
        {isRegister ? '已有帳號？' : '沒有帳號？'}
        <button onClick={() => setIsRegister(!isRegister)}>{isRegister ? '登入' : '註冊'}</button>
      </p>
    </div>
  );
}

function Logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.location.href = '/';
  return null;
}

function App() {
  const [user, setUser] = useState(() => {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
  });

  return (
    <ApolloProvider client={client}>
      <BrowserRouter>
        <div className="container">
          <Routes>
            <Route path="/" element={<Feed user={user} />} />
            <Route path="/post/:id" element={<PostDetail />} />
            <Route path="/user/:id" element={<UserProfile />} />
            <Route path="/login" element={<LoginForm onLogin={setUser} />} />
            <Route path="/logout" element={<Logout />} />
          </Routes>
        </div>
      </BrowserRouter>
    </ApolloProvider>
  );
}

export default App;