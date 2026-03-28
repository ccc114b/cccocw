from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('todo.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/todos', methods=['GET'])
def get_todos():
    conn = get_db_connection()
    todos = conn.execute('SELECT * FROM todos ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in todos])

@app.route('/api/todos', methods=['POST'])
def add_todo():
    data = request.get_json()
    title = data.get('title', '')
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.execute('INSERT INTO todos (title, completed) VALUES (?, 0)', (title,))
    conn.commit()
    todo_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'id': todo_id, 'title': title, 'completed': 0}), 201

@app.route('/api/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    data = request.get_json()
    completed = data.get('completed', 0)
    
    conn = get_db_connection()
    conn.execute('UPDATE todos SET completed = ? WHERE id = ?', (completed, id))
    conn.commit()
    conn.close()
    
    return jsonify({'id': id, 'completed': completed})

@app.route('/api/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM todos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Deleted successfully'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)