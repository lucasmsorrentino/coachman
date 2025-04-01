import sqlite3

DB_NAME = "scores.db"

def init_db():
    """Initialize the database and create the scores table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name CHAR(3) NOT NULL,
            score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 9999),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def insert_score(player_name, score):
    """Insert a new score into the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO scores (player_name, score) VALUES (?, ?)', 
                  (player_name[:3].upper(), score))
    conn.commit()
    conn.close()

def get_high_scores(limit=10):
    """Return a list of high scores sorted in descending order."""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT player_name, score, strftime('%Y-%m-%d', created_at) 
        FROM scores 
        ORDER BY score DESC 
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    processed_scores = []
    for row in rows:
        player_name, score, created_at = row  # Unpack the tuple
        # Check if score is None (shouldn't happen with your schema)
        if score is None:
            score = 0
        processed_scores.append((player_name, score, created_at))
    return processed_scores


if __name__ == '__main__':
    init_db()
