from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    completed INTEGER DEFAULT 0
                )''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('SELECT * FROM todos ORDER BY id DESC')
    todos = c.fetchall()
    conn.close()
    return render_template('index.html', todos=todos)

@app.route('/add', methods=['POST'])
def add():
    task = request.form.get('task')
    if task:
        conn = sqlite3.connect('todo.db')
        c = conn.cursor()
        c.execute('INSERT INTO todos (task) VALUES (?)', (task,))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:todo_id>')
def delete(todo_id):
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/toggle/<int:todo_id>')
def toggle(todo_id):
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('SELECT completed FROM todos WHERE id = ?', (todo_id,))
    current = c.fetchone()[0]
    new_status = 0 if current == 1 else 1
    c.execute('UPDATE todos SET completed = ? WHERE id = ?', (new_status, todo_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)