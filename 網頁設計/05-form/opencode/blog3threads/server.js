const express = require('express');
const session = require('express-session');
const bcrypt = require('bcryptjs');
const db = require('./database');
const marked = require('marked');

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(session({
  secret: 'blog-secret-key',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 24 * 60 * 60 * 1000 }
}));

function getUserPosts(userId, callback) {
  db.all('SELECT * FROM posts WHERE author_id = ? ORDER BY created_at DESC', [userId], (err, rows) => {
    callback(err, rows);
  });
}

function getAllPosts(callback) {
  db.all('SELECT posts.*, users.username FROM posts LEFT JOIN users ON posts.author_id = users.id ORDER BY created_at DESC', [], (err, rows) => {
    callback(err, rows);
  });
}

function getUserById(userId, callback) {
  db.get('SELECT * FROM users WHERE id = ?', [userId], (err, row) => {
    callback(err, row);
  });
}

function getPost(id, callback) {
  db.get('SELECT posts.*, users.username FROM posts LEFT JOIN users ON posts.author_id = users.id WHERE posts.id = ?', [id], (err, row) => {
    callback(err, row);
  });
}

function addPost(content, authorId, callback) {
  db.run('INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)', [content.substring(0, 50), content, authorId], function(err) {
    callback(err, this.lastID);
  });
}

function deletePost(id, userId, callback) {
  db.run('DELETE FROM posts WHERE id = ? AND author_id = ?', [id, userId], function(err) {
    callback(err);
  });
}

function findUser(username, callback) {
  db.get('SELECT * FROM users WHERE username = ?', [username], (err, row) => {
    callback(err, row);
  });
}

function createUser(username, password, callback) {
  bcrypt.hash(password, 10, (err, hash) => {
    if (err) return callback(err);
    db.run('INSERT INTO users (username, password) VALUES (?, ?)', [username, hash], function(err) {
      callback(err, this.lastID);
    });
  });
}

function requireLogin(req, res, next) {
  if (!req.session.userId) {
    return res.redirect('/login');
  }
  next();
}

app.use((req, res, next) => {
  res.locals.userId = req.session.userId;
  res.locals.username = req.session.username;
  next();
});

const layout = (title, content) => `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${title}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #000; color: #fff; min-height: 100vh; }
    .container { display: flex; min-height: 100vh; }
    .sidebar { width: 280px; padding: 20px; border-right: 1px solid #2d2d2d; position: fixed; height: 100vh; }
    .main { margin-left: 280px; flex: 1; max-width: 700px; min-height: 100vh; border-right: 1px solid #2d2d2d; }
    .logo { font-size: 24px; font-weight: bold; padding: 15px 0; margin-bottom: 20px; }
    .logo a { color: #fff; text-decoration: none; }
    .nav-item { padding: 15px; font-size: 18px; border-radius: 30px; margin-bottom: 5px; display: block; color: #fff; text-decoration: none; }
    .nav-item:hover { background: #1a1a1a; }
    .nav-item.active { font-weight: bold; }
    .user-profile { padding: 15px; border-radius: 30px; display: flex; align-items: center; gap: 12px; margin-top: 20px; background: #1a1a1a; }
    .avatar { width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; }
    .user-info { flex: 1; }
    .user-name { font-weight: bold; }
    .user-handle { color: #71767b; font-size: 14px; }
    .btn { padding: 10px 20px; border-radius: 20px; border: none; cursor: pointer; font-size: 14px; font-weight: bold; }
    .btn-primary { background: #fff; color: #000; width: 100%; }
    .btn-primary:hover { background: #e6e6e6; }
    .header { padding: 20px; border-bottom: 1px solid #2d2d2d; position: sticky; top: 0; background: rgba(0,0,0,0.8); backdrop-filter: blur(10px); z-index: 100; }
    .header h1 { font-size: 20px; font-weight: bold; }
    .post-form { padding: 20px; border-bottom: 1px solid #2d2d2d; }
    .post-form textarea { width: 100%; background: transparent; border: none; color: #fff; font-size: 18px; resize: none; min-height: 80px; outline: none; }
    .post-form textarea::placeholder { color: #71767b; }
    .post-form-actions { display: flex; justify-content: flex-end; margin-top: 10px; }
    .post { padding: 20px; border-bottom: 1px solid #2d2d2d; cursor: pointer; transition: background 0.2s; }
    .post:hover { background: #0a0a0a; }
    .post-header { display: flex; gap: 12px; margin-bottom: 10px; }
    .post-avatar { width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; font-weight: bold; }
    .post-user-info { flex: 1; }
    .post-name { font-weight: bold; }
    .post-name a { color: #fff; text-decoration: none; }
    .post-name a:hover { text-decoration: underline; }
    .post-handle { color: #71767b; }
    .post-time { color: #71767b; }
    .post-content { font-size: 16px; line-height: 1.5; margin-bottom: 12px; white-space: pre-wrap; }
    .delete-btn { color: #f4212e; cursor: pointer; margin-left: auto; }
    .empty-state { text-align: center; padding: 60px 20px; color: #71767b; }
    input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #2d2d2d; background: #000; color: #fff; font-size: 16px; }
    .form-container { max-width: 400px; margin: 100px auto; padding: 30px; }
    .form-title { font-size: 28px; font-weight: bold; margin-bottom: 30px; }
    .auth-links { margin-top: 20px; text-align: center; color: #71767b; }
    .auth-links a { color: #1d9bf0; text-decoration: none; }
    .back-link { color: #1d9bf0; text-decoration: none; padding: 20px; display: block; border-bottom: 1px solid #2d2d2d; }
  </style>
</head>
<body>
  ${content}
</body>
</html>`;

const sidebar = (req, currentPage) => {
  if (!req.session.userId) {
    return `
      <div class="sidebar">
        <div class="logo"><a href="/">Threads</a></div>
        <a href="/login" class="nav-item ${currentPage === 'login' ? 'active' : ''}">Login</a>
        <a href="/register" class="nav-item ${currentPage === 'register' ? 'active' : ''}">Register</a>
      </div>
    `;
  }
  return `
    <div class="sidebar">
      <div class="logo"><a href="/">Threads</a></div>
      <a href="/" class="nav-item ${currentPage === 'public' ? 'active' : ''}">Public</a>
      <a href="/my" class="nav-item ${currentPage === 'my' ? 'active' : ''}">My Posts</a>
      
      <div class="user-profile">
        <div class="avatar">${req.session.username[0].toUpperCase()}</div>
        <div class="user-info">
          <div class="user-name">${req.session.username}</div>
          <div class="user-handle">@${req.session.username}</div>
        </div>
      </div>
      <a href="/logout" class="nav-item" style="margin-top: 20px;">Log out</a>
    </div>
  `;
};

app.get('/', (req, res) => {
  if (!req.session.userId) {
    return res.redirect('/login');
  }
  
  getAllPosts((err, allPosts) => {
    if (err) return res.status(500).send('Error');
    
    const content = `
      <div class="container">
        ${req.session.userId ? sidebar(req, 'public') : ''}
        <div class="main" style="${!req.session.userId ? 'margin-left: 0; max-width: none; border: none;' : ''}">
          <div class="header">
            <h1>Public Posts</h1>
          </div>
          
          ${allPosts.length === 0 
            ? '<div class="empty-state">No posts yet.</div>'
            : allPosts.map(post => `
              <div class="post">
                <div class="post-header">
                  <div class="post-avatar">${(post.username || '?')[0].toUpperCase()}</div>
                  <div class="post-user-info">
                    <span class="post-name"><a href="/user/${post.author_id}">${post.username || 'Unknown'}</a></span>
                    <span class="post-handle">@${post.username || 'unknown'}</span>
                    <span class="post-time"> · ${new Date(post.created_at).toLocaleString()}</span>
                  </div>
                </div>
                <div class="post-content">${post.content}</div>
              </div>
            `).join('')}
        </div>
      </div>
    `;
    
    res.send(layout('Threads', content));
  });
});

app.get('/my', requireLogin, (req, res) => {
  getUserPosts(req.session.userId, (err, userPosts) => {
    if (err) return res.status(500).send('Error');
    
    const content = `
      <div class="container">
        ${sidebar(req, 'my')}
        <div class="main">
          <div class="header">
            <h1>My Posts</h1>
          </div>
          
          <div class="post-form">
            <form method="post" action="/posts">
              <textarea name="content" placeholder="What is on your mind?" required></textarea>
              <div class="post-form-actions">
                <button type="submit" class="btn btn-primary">Post</button>
              </div>
            </form>
          </div>
          
          ${userPosts.length === 0 
            ? '<div class="empty-state">No posts yet. Share something!</div>'
            : userPosts.map(post => `
              <div class="post">
                <div class="post-header">
                  <div class="post-avatar">${req.session.username[0].toUpperCase()}</div>
                  <div class="post-user-info">
                    <span class="post-name">${req.session.username}</span>
                    <span class="post-handle">@${req.session.username}</span>
                    <span class="post-time"> · ${new Date(post.created_at).toLocaleString()}</span>
                  </div>
                  <span class="delete-btn" onclick="if(confirm('Delete this post?')) fetch('/post/${post.id}', {method: 'DELETE'}).then(() => location.reload())">✕</span>
                </div>
                <div class="post-content">${post.content}</div>
              </div>
            `).join('')}
        </div>
      </div>
    `;
    
    res.send(layout('My Posts', content));
  });
});

app.get('/user/:id', (req, res) => {
  const userId = parseInt(req.params.id);
  
  getUserById(userId, (err, user) => {
    if (err || !user) return res.status(404).send('User not found');
    
    getUserPosts(userId, (err, posts) => {
      if (err) return res.status(500).send('Error');
      
      const isOwner = req.session.userId === userId;
      const content = `
        <div class="container">
          ${req.session.userId ? sidebar(req, '') : ''}
          <div class="main" style="${!req.session.userId ? 'margin-left: 0; max-width: none; border: none;' : ''}">
            <a href="/" class="back-link">← Back</a>
            <div class="header">
              <h1>@${user.username}'s Posts</h1>
            </div>
            
            ${posts.length === 0 
              ? '<div class="empty-state">No posts yet.</div>'
              : posts.map(post => `
                <div class="post">
                  <div class="post-header">
                    <div class="post-avatar">${user.username[0].toUpperCase()}</div>
                    <div class="post-user-info">
                      <span class="post-name"><a href="/user/${user.id}">${user.username}</a></span>
                      <span class="post-handle">@${user.username}</span>
                      <span class="post-time"> · ${new Date(post.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                  <div class="post-content">${post.content}</div>
                </div>
              `).join('')}
          </div>
        </div>
      `;
      
      res.send(layout(`@${user.username}`, content));
    });
  });
});

app.get('/post/:id', (req, res) => {
  getPost(req.params.id, (err, post) => {
    if (err || !post) return res.status(404).send('Post not found');
    
    const content = `
      <div class="container">
        ${req.session.userId ? sidebar(req, '') : ''}
        <div class="main" style="${!req.session.userId ? 'margin-left: 0; max-width: none; border: none;' : ''}">
          <a href="/" class="back-link">← Back</a>
          <div class="post">
            <div class="post-header">
              <div class="post-avatar">${(post.username || '?')[0].toUpperCase()}</div>
              <div class="post-user-info">
                <span class="post-name"><a href="/user/${post.author_id}">${post.username || 'Unknown'}</a></span>
                <span class="post-handle">@${post.username || 'unknown'}</span>
                <span class="post-time"> · ${new Date(post.created_at).toLocaleString()}</span>
              </div>
            </div>
            <div class="post-content" style="font-size: 20px;">${post.content}</div>
          </div>
        </div>
      </div>
    `;
    res.send(layout(post.content.substring(0, 50), content));
  });
});

app.post('/posts', requireLogin, (req, res) => {
  const { content } = req.body;
  if (!content) return res.status(400).send('Content required');
  
  addPost(content, req.session.userId, (err, id) => {
    if (err) return res.status(500).send('Error saving post');
    res.redirect('/my');
  });
});

app.delete('/post/:id', requireLogin, (req, res) => {
  deletePost(req.params.id, req.session.userId, (err) => {
    if (err) return res.status(500).send('Error');
    res.json({ success: true });
  });
});

app.get('/login', (req, res) => {
  if (req.session.userId) return res.redirect('/');
  
  const content = `
    <div class="container">
      ${sidebar(req, 'login')}
      <div class="main" style="margin-left: 280px;">
        <div class="form-container" style="margin-top: 50px;">
          <h1 class="form-title">Log in to Threads</h1>
          <form method="post" action="/login">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit" class="btn btn-primary">Log in</button>
          </form>
          <div class="auth-links">
            Don't have an account? <a href="/register">Sign up</a>
          </div>
        </div>
      </div>
    </div>
  `;
  res.send(layout('Login', content));
});

app.post('/login', (req, res) => {
  const { username, password } = req.body;
  
  findUser(username, (err, user) => {
    if (err || !user) return res.status(401).send('Invalid credentials');
    
    bcrypt.compare(password, user.password, (err, match) => {
      if (err || !match) return res.status(401).send('Invalid credentials');
      
      req.session.userId = user.id;
      req.session.username = user.username;
      res.redirect('/');
    });
  });
});

app.get('/register', (req, res) => {
  if (req.session.userId) return res.redirect('/');
  
  const content = `
    <div class="container">
      ${sidebar(req, 'register')}
      <div class="main" style="margin-left: 280px;">
        <div class="form-container" style="margin-top: 50px;">
          <h1 class="form-title">Create account</h1>
          <form method="post" action="/register">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit" class="btn btn-primary">Sign up</button>
          </form>
          <div class="auth-links">
            Have an account? <a href="/login">Log in</a>
          </div>
        </div>
      </div>
    </div>
  `;
  res.send(layout('Register', content));
});

app.post('/register', (req, res) => {
  const { username, password } = req.body;
  
  if (!username || !password) return res.status(400).send('Required');
  
  createUser(username, password, (err, id) => {
    if (err) {
      if (err.message.includes('UNIQUE')) {
        return res.status(400).send('Username exists');
      }
      return res.status(500).send('Error');
    }
    res.redirect('/login');
  });
});

app.get('/logout', (req, res) => {
  req.session.destroy();
  res.redirect('/');
});

app.listen(3000, () => {
  console.log('Blog running at http://localhost:3000');
});