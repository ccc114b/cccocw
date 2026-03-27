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

function getPosts(callback) {
  db.all('SELECT posts.*, users.username FROM posts LEFT JOIN users ON posts.author_id = users.id ORDER BY created_at DESC', [], (err, rows) => {
    callback(err, rows);
  });
}

function getPost(id, callback) {
  db.get('SELECT posts.*, users.username FROM posts LEFT JOIN users ON posts.author_id = users.id WHERE posts.id = ?', [id], (err, row) => {
    callback(err, row);
  });
}

function addPost(title, content, authorId, callback) {
  db.run('INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)', [title, content, authorId], function(err) {
    callback(err, this.lastID);
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

app.get('/', (req, res) => {
  getPosts((err, posts) => {
    if (err) return res.status(500).send('Error loading posts');
    
    let html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>My Blog</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
    h1 { border-bottom: 2px solid #333; padding-bottom: 10px; }
    .post { margin-bottom: 30px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
    .post h2 { margin-top: 0; }
    .post a { text-decoration: none; color: #333; }
    .post a:hover { color: #0066cc; }
    .meta { color: #666; font-size: 0.9em; }
    .new-post { background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 30px; }
    input, textarea { width: 100%; padding: 10px; margin: 5px 0; box-sizing: border-box; }
    button { background: #333; color: white; padding: 10px 20px; border: none; cursor: pointer; }
    button:hover { background: #555; }
    .nav { margin-bottom: 20px; }
    .nav a { margin-right: 15px; }
    .error { color: red; }
  </style>
</head>
<body>
  <div class="nav">
    ${res.locals.userId 
      ? `<span>Welcome, ${res.locals.username}!</span> <a href="/logout">Logout</a>` 
      : `<a href="/login">Login</a> <a href="/register">Register</a>`}
  </div>
  <h1>My Blog</h1>`;

    if (res.locals.userId) {
      html += `<div class="new-post">
        <h3>New Post</h3>
        <form method="post" action="/posts">
          <input type="text" name="title" placeholder="Title" required>
          <textarea name="content" rows="5" placeholder="Content (Markdown supported)" required></textarea>
          <button type="submit">Publish</button>
        </form>
      </div>`;
    }

    posts.forEach(post => {
      html += `<div class="post">
      <h2><a href="/post/${post.id}">${post.title}</a></h2>
      <p class="meta">${new Date(post.created_at).toLocaleString()} by ${post.username || 'Unknown'}</p>
      <p>${post.content.substring(0, 200)}...</p>
      <a href="/post/${post.id}">Read more →</a>
    </div>`;
    });

    html += `</body></html>`;
    res.send(html);
  });
});

app.get('/post/:id', (req, res) => {
  getPost(req.params.id, (err, post) => {
    if (err || !post) return res.status(404).send('Post not found');
    
    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${post.title}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
    a { color: #333; }
    .meta { color: #666; }
    .content { line-height: 1.8; }
    .content img { max-width: 100%; }
    .nav { margin-bottom: 20px; }
  </style>
</head>
<body>
  <div class="nav">
    <a href="/">← Back</a>
    ${res.locals.userId 
      ? ` | <a href="/logout">Logout</a>` 
      : ` | <a href="/login">Login</a>`}
  </div>
  <h1>${post.title}</h1>
  <p class="meta">${new Date(post.created_at).toLocaleString()} by ${post.username || 'Unknown'}</p>
  <div class="content">${marked.parse(post.content)}</div>
</body></html>`;
    res.send(html);
  });
});

app.post('/posts', requireLogin, (req, res) => {
  const { title, content } = req.body;
  if (!title || !content) return res.status(400).send('Title and content required');
  
  addPost(title, content, req.session.userId, (err, id) => {
    if (err) return res.status(500).send('Error saving post');
    res.redirect('/');
  });
});

app.get('/login', (req, res) => {
  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Login</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
    input { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
    button { background: #333; color: white; padding: 10px 20px; border: none; cursor: pointer; width: 100%; }
    a { color: #333; }
    .error { color: red; }
  </style>
</head>
<body>
  <h1>Login</h1>
  <form method="post" action="/login">
    <input type="text" name="username" placeholder="Username" required>
    <input type="password" name="password" placeholder="Password" required>
    <button type="submit">Login</button>
  </form>
  <p>No account? <a href="/register">Register</a></p>
</body></html>`;
  res.send(html);
});

app.post('/login', (req, res) => {
  const { username, password } = req.body;
  
  findUser(username, (err, user) => {
    if (err || !user) return res.status(401).send('Invalid username or password');
    
    bcrypt.compare(password, user.password, (err, match) => {
      if (err || !match) return res.status(401).send('Invalid username or password');
      
      req.session.userId = user.id;
      req.session.username = user.username;
      res.redirect('/');
    });
  });
});

app.get('/register', (req, res) => {
  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Register</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
    input { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
    button { background: #333; color: white; padding: 10px 20px; border: none; cursor: pointer; width: 100%; }
    a { color: #333; }
  </style>
</head>
<body>
  <h1>Register</h1>
  <form method="post" action="/register">
    <input type="text" name="username" placeholder="Username" required>
    <input type="password" name="password" placeholder="Password" required>
    <button type="submit">Register</button>
  </form>
  <p>Have account? <a href="/login">Login</a></p>
</body></html>`;
  res.send(html);
});

app.post('/register', (req, res) => {
  const { username, password } = req.body;
  
  if (!username || !password) return res.status(400).send('Username and password required');
  
  createUser(username, password, (err, id) => {
    if (err) {
      if (err.message.includes('UNIQUE')) {
        return res.status(400).send('Username already exists');
      }
      return res.status(500).send('Error creating user');
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