from flask import Flask, g, render_template
import sqlite3
from pathlib import Path

DB_PATH = Path("app.db")
SCHEMA = """
CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP,
    note TEXT
);
"""

app = Flask(__name__)

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.execute("INSERT INTO visits (note) VALUES (?)", ("hello world",))
    db.commit()

@app.route("/")
def index():
    db = get_db()
    rows = db.execute("SELECT id, ts, note FROM visits ORDER BY ts DESC LIMIT 10").fetchall()
    return render_template("index.html", visits=rows)

if __name__ == "__main__":
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with app.app_context():
        init_db()
    app.run(debug=True)
