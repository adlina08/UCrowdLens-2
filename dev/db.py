import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "ucrowdlens.db")

def query(sql, args=()):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute(sql, args).fetchall()
        conn.commit()
        return rows
    finally:
        conn.close()


def init_db():
    query("""
        CREATE TABLE IF NOT EXISTS ADMIN (
            ADMINID INTEGER PRIMARY KEY AUTOINCREMENT,
            USERNAME TEXT NOT NULL UNIQUE,
            PASSWORD TEXT NOT NULL
        )
    """)

    query("""
        CREATE TABLE IF NOT EXISTS LOCATION (
            LOCATIONID INTEGER PRIMARY KEY AUTOINCREMENT,
            LOCATION_NAME TEXT NOT NULL,
            STATUS TEXT NOT NULL DEFAULT 'active'
        )
    """)

    query("""
        CREATE TABLE IF NOT EXISTS THRESHOLD (
            THRESHOLDID INTEGER PRIMARY KEY,
            LOW INTEGER NOT NULL,
            MEDIUM INTEGER NOT NULL
        )
    """)

    query("""
        CREATE TABLE IF NOT EXISTS CROWD_LOG (
            LOGID INTEGER PRIMARY KEY AUTOINCREMENT,
            TIMESTAMP TEXT NOT NULL,
            CROWD_COUNT INTEGER NOT NULL,
            DENSITY_LEVEL TEXT NOT NULL,
            LOCATIONID INTEGER NOT NULL
                REFERENCES LOCATION(LOCATIONID)
        )
    """)

    # Create default admin only if no admin exists
    if not query("SELECT 1 FROM ADMIN"):
        query(
            "INSERT INTO ADMIN (USERNAME, PASSWORD) VALUES (?, ?)",
            ("admin", "admin123")
        )

    # Create default threshold only if it does not exist
    if not query("SELECT 1 FROM THRESHOLD WHERE THRESHOLDID=1"):
        query("INSERT INTO THRESHOLD VALUES (1, 10, 20)")

    # Create default locations only if they do not exist
    for name in [
        "Bus Stop Dataran Cendekia, UiTM Shah Alam",
        "Cafeteria, UiTM Shah Alam"
    ]:
        if not query(
            "SELECT 1 FROM LOCATION WHERE LOCATION_NAME=?",
            (name,)
        ):
            query(
                "INSERT INTO LOCATION (LOCATION_NAME) VALUES (?)",
                (name,)
            )


if __name__ == "__main__":
    init_db()
    print("Database created successfully!")
    print("Database location:", DB)