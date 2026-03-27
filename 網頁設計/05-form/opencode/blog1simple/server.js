const express = require('express');
const db = require('./database');
const marked = require('marked');

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

function getPosts(callback) {
  db.all('SELECT id, title, substr(content, 1, 200) as excerpt, created_at FROM posts ORDER BY created_at DESC', [], (err, rows) => {
    callback(err, rows);
  });
}

function getPost(id, callback) {
  db.get('SELECT * FROM posts WHERE id = ?', [id], (err, row) => {
    callback(err, row);
  });
}

function addPost(title, content, callback) {
  db.run('INSERT INTO posts (title, content) VALUES (?, ?)', [title, content], function(err) {
    callback(err, this.lastID);
  });
}

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
  </style>
</head>
<body>
  <h1>My Blog</h1>
  <div class="new-post">
    <h3>New Post</h3>
    <form method="post" action="/posts">
      <input type="text" name="title" placeholder="Title" required>
      <textarea name="content" rows="5" placeholder="Content (Markdown supported)" required></textarea>
      <button type="submit">Publish</button>
    </form>
  </div>`;

    posts.forEach(post => {
      html += `<div class="post">
      <h2><a href="/post/${post.id}">${post.title}</a></h2>
      <p class="meta">${new Date(post.created_at).toLocaleString()}</p>
      <p>${post.excerpt}...</p>
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
  </style>
</head>
<body>
  <p><a href="/">← Back</a></p>
  <h1>${post.title}</h1>
  <p class="meta">${new Date(post.created_at).toLocaleString()}</p>
  <div class="content">${marked.parse(post.content)}</div>
</body></html>`;
    res.send(html);
  });
});

app.post('/posts', (req, res) => {
  const { title, content } = req.body;
  if (!title || !content) return res.status(400).send('Title and content required');
  
  addPost(title, content, (err, id) => {
    if (err) return res.status(500).send('Error saving post');
    res.redirect('/');
  });
});

app.listen(3000, () => {
  console.log('Blog running at http://localhost:3000');
});