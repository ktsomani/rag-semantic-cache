import sqlite3
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ExtractionAttempt:
    doc_path: str
    stage: str
    success: bool
    word_count: int
    error_category: str | None

def init_extraction_db(db_path: str = "ingestion/extraction_log.db"):
    """Initializes the SQLite database for tracking extraction attempts."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_path TEXT,
            stage TEXT,
            success INTEGER,
            word_count INTEGER,
            error_category TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_attempt(attempt: ExtractionAttempt, db_path: str = "ingestion/extraction_log.db"):
    """Logs a single extraction attempt to the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO attempts (doc_path, stage, success, word_count, error_category)
        VALUES (?, ?, ?, ?, ?)
    ''', (attempt.doc_path, attempt.stage, int(attempt.success), attempt.word_count, attempt.error_category))
    conn.commit()
    conn.close()

def load_document(file_path: str) -> ExtractionAttempt:
    """
    Placeholder for the fallback chain (pdftotext -> fitz -> OCR).
    For now, we just simulate a successful text load.
    """
    path = Path(file_path)
    if not path.exists():
        return ExtractionAttempt(str(path), "none", False, 0, "file_not_found")
        
    # Simulate reading a text file
    try:
        text = path.read_text(encoding="utf-8")
        words = len(text.split())
        if words == 0:
            return ExtractionAttempt(str(path), "txt_reader", False, 0, "empty_text")
        return ExtractionAttempt(str(path), "txt_reader", True, words, None)
    except Exception as e:
        return ExtractionAttempt(str(path), "txt_reader", False, 0, str(type(e).__name__))