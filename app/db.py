"""
app.db
Gestión simple de la base de datos SQLite para leads y citas.
Usa sqlite3 y crea dos tablas: leads y appointments.
"""
import sqlite3
from sqlite3 import Connection
import os
from typing import Optional, Dict, Any


def get_connection(db_path: str) -> Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str):
    conn = get_connection(db_path)
    cur = conn.cursor()
    # Crear tabla leads
    cur.execute('''
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        interest TEXT,
        qualification TEXT,
        created_at TEXT
    )
    ''')

    # Crear tabla appointments
    cur.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        date TEXT,
        time TEXT,
        type TEXT,
        status TEXT,
        created_at TEXT,
        FOREIGN KEY(lead_id) REFERENCES leads(id)
    )
    ''')
    conn.commit()
    return conn


def insert_lead(conn: Connection, lead: Dict[str, Any]) -> int:
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO leads (name, phone, interest, qualification, created_at) VALUES (?, ?, ?, ?, ?)',
        (lead.get('name'), lead.get('phone'), lead.get('interest'), lead.get('qualification'), lead.get('created_at'))
    )
    conn.commit()
    return cur.lastrowid


def insert_appointment(conn: Connection, appointment: Dict[str, Any]) -> int:
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO appointments (lead_id, date, time, type, status, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        (appointment.get('lead_id'), appointment.get('date'), appointment.get('time'), appointment.get('type'), appointment.get('status'), appointment.get('created_at'))
    )
    conn.commit()
    return cur.lastrowid


def get_stats(conn: Connection) -> Dict[str, int]:
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) as total_leads FROM leads')
    total_leads = cur.fetchone()['total_leads']
    cur.execute('SELECT COUNT(*) as total_appts FROM appointments')
    total_appts = cur.fetchone()['total_appts']
    return {'total_leads': total_leads, 'total_appointments': total_appts}
