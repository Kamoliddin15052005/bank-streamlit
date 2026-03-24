import os
import sqlite3

# ─── DATABASE URL — Streamlit secrets yoki env ─────────────
def _get_db_url():
    # 1. Streamlit Cloud secrets (asosiy usul)
    try:
        import streamlit as st
        url = st.secrets.get("DATABASE_URL", "")
        if url:
            return url
    except Exception:
        pass
    # 2. Environment variable (lokal ishlatish uchun)
    return os.getenv("DATABASE_URL", "")

DATABASE_URL = _get_db_url()
USE_PG = bool(DATABASE_URL)

def get_conn():
    global USE_PG
    if USE_PG:
        try:
            import psycopg2
            import psycopg2.extras
            url = DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
            return conn
        except Exception as e:
            import streamlit as st
            st.error(f"⚠️ PostgreSQL ulanmadi: {e}\n\nIltimos, Streamlit Secrets'da DATABASE_URL ni tekshiring yoki o'chiring (SQLite ishlatish uchun).")
            st.stop()
    else:
        conn = sqlite3.connect("bank_assets.db", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

def _fetchall(cur):
    rows = cur.fetchall()
    return [dict(r) for r in rows]

def _fetchone(cur):
    r = cur.fetchone()
    return dict(r) if r else None

def init_db():
    conn = get_conn()
    if USE_PG:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS assets (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'IT',
            serial_number TEXT UNIQUE NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'REGISTERED',
            image_url TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS employees (
            id SERIAL PRIMARY KEY,
            full_name TEXT NOT NULL,
            employee_id TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            branch TEXT, email TEXT, phone TEXT,
            created_at TIMESTAMP DEFAULT NOW())""")
        cur.execute("""CREATE TABLE IF NOT EXISTS assignments (
            id SERIAL PRIMARY KEY,
            asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
            employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
            department TEXT, branch TEXT, notes TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            assigned_at TIMESTAMP DEFAULT NOW(),
            returned_at TIMESTAMP)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS asset_history (
            id SERIAL PRIMARY KEY,
            asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
            action TEXT NOT NULL,
            old_status TEXT, new_status TEXT,
            changed_by TEXT NOT NULL DEFAULT 'admin',
            reason TEXT, details TEXT,
            created_at TIMESTAMP DEFAULT NOW())""")
        conn.commit()
    else:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, asset_type TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'IT',
            serial_number TEXT UNIQUE NOT NULL,
            description TEXT, status TEXT NOT NULL DEFAULT 'REGISTERED',
            image_url TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT);
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL, employee_id TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL, branch TEXT, email TEXT, phone TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL, employee_id INTEGER,
            department TEXT, branch TEXT, notes TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
            returned_at TEXT);
        CREATE TABLE IF NOT EXISTS asset_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL, action TEXT NOT NULL,
            old_status TEXT, new_status TEXT,
            changed_by TEXT NOT NULL DEFAULT 'admin',
            reason TEXT, details TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')));
        """)
        conn.commit()
    conn.close()

# ─── CONSTANTS ─────────────────────────────────────────────
ALLOWED = {
    "REGISTERED":  ["ASSIGNED", "WRITTEN_OFF"],
    "ASSIGNED":    ["IN_REPAIR", "LOST", "REGISTERED", "WRITTEN_OFF"],
    "IN_REPAIR":   ["ASSIGNED", "REGISTERED", "WRITTEN_OFF"],
    "LOST":        ["WRITTEN_OFF"],
    "WRITTEN_OFF": [],
}
STATUS_UZ = {
    "REGISTERED":  "Ro'yxatda",
    "ASSIGNED":    "Tayinlangan",
    "IN_REPAIR":   "Ta'mirlashda",
    "LOST":        "Yo'qolgan",
    "WRITTEN_OFF": "Hisobdan chiqarilgan",
}
STATUS_COLORS = {
    "REGISTERED": "🔵", "ASSIGNED": "🟢",
    "IN_REPAIR": "🟡", "LOST": "🔴", "WRITTEN_OFF": "⚫",
}
CATEGORIES  = ["IT", "OFFICE", "SECURITY", "FURNITURE", "OTHER"]
DEPARTMENTS = ["IT","Moliya","Buxgalteriya","HR","Marketing","Xavfsizlik","Boshqaruv","Mijozlar xizmati"]

# ─── ASSETS ────────────────────────────────────────────────
def get_assets(search="", status="", category=""):
    conn = get_conn()
    if USE_PG:
        q = "SELECT * FROM assets WHERE 1=1"; p = []
        if search:
            q += " AND (name ILIKE %s OR serial_number ILIKE %s OR asset_type ILIKE %s)"
            p += [f"%{search}%"]*3
        if status:  q += " AND status = %s"; p.append(status)
        if category: q += " AND category = %s"; p.append(category)
        q += " ORDER BY id DESC"
        cur = conn.cursor(); cur.execute(q, p)
        rows = _fetchall(cur); conn.close(); return rows
    else:
        q = "SELECT * FROM assets WHERE 1=1"; p = []
        if search:
            q += " AND (name LIKE ? OR serial_number LIKE ? OR asset_type LIKE ?)"
            p += [f"%{search}%"]*3
        if status:  q += " AND status = ?"; p.append(status)
        if category: q += " AND category = ?"; p.append(category)
        q += " ORDER BY id DESC"
        rows = conn.execute(q, p).fetchall()
        conn.close(); return [dict(r) for r in rows]

def get_asset(asset_id):
    conn = get_conn()
    if USE_PG:
        cur = conn.cursor(); cur.execute("SELECT * FROM assets WHERE id=%s", (asset_id,))
        r = _fetchone(cur); conn.close(); return r
    else:
        r = conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
        conn.close(); return dict(r) if r else None

def create_asset(name, asset_type, category, serial_number, description=""):
    conn = get_conn()
    try:
        if USE_PG:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO assets (name,asset_type,category,serial_number,description) VALUES (%s,%s,%s,%s,%s) RETURNING id",
                (name, asset_type, category, serial_number, description))
            asset_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO asset_history (asset_id,action,new_status,changed_by,details) VALUES (%s,%s,%s,%s,%s)",
                (asset_id,"CREATED","REGISTERED","admin",f"'{name}' ro'yxatga olindi"))
        else:
            conn.execute(
                "INSERT INTO assets (name,asset_type,category,serial_number,description) VALUES (?,?,?,?,?)",
                (name, asset_type, category, serial_number, description))
            asset_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT INTO asset_history (asset_id,action,new_status,changed_by,details) VALUES (?,?,?,?,?)",
                (asset_id,"CREATED","REGISTERED","admin",f"'{name}' ro'yxatga olindi"))
        conn.commit(); conn.close()
        return True, "Aktiv muvaffaqiyatli qo'shildi!"
    except Exception as e:
        conn.close()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return False, "Bu seriya raqami allaqachon mavjud!"
        return False, str(e)

def update_asset(asset_id, name, asset_type, category, description):
    conn = get_conn()
    if USE_PG:
        cur = conn.cursor()
        cur.execute("UPDATE assets SET name=%s,asset_type=%s,category=%s,description=%s,updated_at=NOW() WHERE id=%s",
                    (name,asset_type,category,description,asset_id))
        cur.execute("INSERT INTO asset_history (asset_id,action,changed_by,details) VALUES (%s,%s,%s,%s)",
                    (asset_id,"UPDATED","admin","Ma'lumotlar yangilandi"))
    else:
        conn.execute("UPDATE assets SET name=?,asset_type=?,category=?,description=?,updated_at=datetime('now') WHERE id=?",
                     (name,asset_type,category,description,asset_id))
        conn.execute("INSERT INTO asset_history (asset_id,action,changed_by,details) VALUES (?,?,?,?)",
                     (asset_id,"UPDATED","admin","Ma'lumotlar yangilandi"))
    conn.commit(); conn.close()

def delete_asset(asset_id):
    conn = get_conn()
    if USE_PG:
        cur = conn.cursor(); cur.execute("DELETE FROM assets WHERE id=%s",(asset_id,))
    else:
        conn.execute("DELETE FROM asset_history WHERE asset_id=?",(asset_id,))
        conn.execute("DELETE FROM assignments WHERE asset_id=?",(asset_id,))
        conn.execute("DELETE FROM assets WHERE id=?",(asset_id,))
    conn.commit(); conn.close()

def change_status(asset_id, new_status, reason="", changed_by="admin"):
    conn = get_conn()
    if USE_PG:
        cur = conn.cursor(); cur.execute("SELECT * FROM assets WHERE id=%s",(asset_id,))
        asset = _fetchone(cur)
    else:
        r = conn.execute("SELECT * FROM assets WHERE id=?",(asset_id,)).fetchone()
        asset = dict(r) if r else None
    if not asset: conn.close(); return False, "Aktiv topilmadi"
    old_status = asset["status"]
    if new_status not in ALLOWED.get(old_status, []):
        conn.close()
        return False, f"{STATUS_UZ[old_status]} → {STATUS_UZ[new_status]} o'tish ruxsat etilmagan!"
    if USE_PG:
        cur = conn.cursor()
        cur.execute("UPDATE assets SET status=%s,updated_at=NOW() WHERE id=%s",(new_status,asset_id))
        if new_status=="REGISTERED" and old_status=="ASSIGNED":
            cur.execute("UPDATE assignments SET is_active=0,returned_at=NOW() WHERE asset_id=%s AND is_active=1",(asset_id,))
        cur.execute("INSERT INTO asset_history (asset_id,action,old_status,new_status,changed_by,reason) VALUES (%s,%s,%s,%s,%s,%s)",
                    (asset_id,"STATUS_CHANGED",old_status,new_status,changed_by,reason))
    else:
        conn.execute("UPDATE assets SET status=?,updated_at=datetime('now') WHERE id=?",(new_status,asset_id))
        if new_status=="REGISTERED" and old_status=="ASSIGNED":
            conn.execute("UPDATE assignments SET is_active=0,returned_at=datetime('now') WHERE asset_id=? AND is_active=1",(asset_id,))
        conn.execute("INSERT INTO asset_history (asset_id,action,old_status,new_status,changed_by,reason) VALUES (?,?,?,?,?,?)",
                     (asset_id,"STATUS_CHANGED",old_status,new_status,changed_by,reason))
    conn.commit(); conn.close()
    return True, f"Status: {STATUS_UZ[old_status]} → {STATUS_UZ[new_status]}"

def get_asset_history(asset_id):
    conn = get_conn()
    if USE_PG:
        cur = conn.cursor()
        cur.execute("SELECT * FROM asset_history WHERE asset_id=%s ORDER BY created_at DESC",(asset_id,))
        rows = _fetchall(cur); conn.close(); return rows
    else:
        rows = conn.execute("SELECT * FROM asset_history WHERE asset_id=? ORDER BY created_at DESC",(asset_id,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

# ─── EMPLOYEES ─────────────────────────────────────────────
def get_employees():
    conn = get_conn()
    if USE_PG:
        cur = conn.cursor(); cur.execute("SELECT * FROM employees ORDER BY id DESC")
        rows = _fetchall(cur); conn.close(); return rows
    else:
        rows = conn.execute("SELECT * FROM employees ORDER BY id DESC").fetchall()
        conn.close(); return [dict(r) for r in rows]

def create_employee(full_name, employee_id, department, branch="", email="", phone=""):
    conn = get_conn()
    try:
        if USE_PG:
            cur = conn.cursor()
            cur.execute("INSERT INTO employees (full_name,employee_id,department,branch,email,phone) VALUES (%s,%s,%s,%s,%s,%s)",
                        (full_name,employee_id,department,branch,email,phone))
        else:
            conn.execute("INSERT INTO employees (full_name,employee_id,department,branch,email,phone) VALUES (?,?,?,?,?,?)",
                         (full_name,employee_id,department,branch,email,phone))
        conn.commit(); conn.close()
        return True, "Xodim muvaffaqiyatli qo'shildi!"
    except Exception as e:
        conn.close()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return False, "Bu xodim ID allaqachon mavjud!"
        return False, str(e)

def delete_employee(emp_id):
    conn = get_conn()
    if USE_PG:
        cur = conn.cursor(); cur.execute("DELETE FROM employees WHERE id=%s",(emp_id,))
    else:
        conn.execute("DELETE FROM employees WHERE id=?",(emp_id,))
    conn.commit(); conn.close()

# ─── ASSIGNMENTS ───────────────────────────────────────────
def get_assignments(active_only=True):
    conn = get_conn()
    q = """SELECT a.*,ast.name as asset_name,ast.serial_number,
                  ast.status as asset_status,ast.category,
                  e.full_name as employee_name,e.department as emp_dept
           FROM assignments a JOIN assets ast ON a.asset_id=ast.id
           LEFT JOIN employees e ON a.employee_id=e.id"""
    if active_only: q += " WHERE a.is_active=1"
    q += " ORDER BY a.assigned_at DESC"
    if USE_PG:
        cur = conn.cursor(); cur.execute(q)
        rows = _fetchall(cur); conn.close(); return rows
    else:
        rows = conn.execute(q).fetchall()
        conn.close(); return [dict(r) for r in rows]

def assign_asset(asset_id, employee_id=None, department="", branch="", notes=""):
    conn = get_conn()
    if USE_PG:
        cur = conn.cursor(); cur.execute("SELECT * FROM assets WHERE id=%s",(asset_id,))
        asset = _fetchone(cur)
    else:
        r = conn.execute("SELECT * FROM assets WHERE id=?",(asset_id,)).fetchone()
        asset = dict(r) if r else None
    if not asset: conn.close(); return False, "Aktiv topilmadi"
    if asset["status"] in ("LOST","WRITTEN_OFF","IN_REPAIR"):
        conn.close(); return False, f"{STATUS_UZ[asset['status']]} aktiv tayinlanmaydi!"
    old_status = asset["status"]
    if USE_PG:
        cur = conn.cursor()
        cur.execute("UPDATE assignments SET is_active=0,returned_at=NOW() WHERE asset_id=%s AND is_active=1",(asset_id,))
        cur.execute("INSERT INTO assignments (asset_id,employee_id,department,branch,notes) VALUES (%s,%s,%s,%s,%s)",
                    (asset_id,employee_id or None,department,branch,notes))
        cur.execute("UPDATE assets SET status='ASSIGNED',updated_at=NOW() WHERE id=%s",(asset_id,))
        cur.execute("INSERT INTO asset_history (asset_id,action,old_status,new_status,changed_by,details) VALUES (%s,%s,%s,%s,%s,%s)",
                    (asset_id,"ASSIGNED",old_status,"ASSIGNED","admin",f"Bo'lim: {department}"))
    else:
        conn.execute("UPDATE assignments SET is_active=0,returned_at=datetime('now') WHERE asset_id=? AND is_active=1",(asset_id,))
        conn.execute("INSERT INTO assignments (asset_id,employee_id,department,branch,notes) VALUES (?,?,?,?,?)",
                     (asset_id,employee_id or None,department,branch,notes))
        conn.execute("UPDATE assets SET status='ASSIGNED',updated_at=datetime('now') WHERE id=?",(asset_id,))
        conn.execute("INSERT INTO asset_history (asset_id,action,old_status,new_status,changed_by,details) VALUES (?,?,?,?,?,?)",
                     (asset_id,"ASSIGNED",old_status,"ASSIGNED","admin",f"Bo'lim: {department}"))
    conn.commit(); conn.close()
    return True, "Aktiv muvaffaqiyatli tayinlandi!"

def return_asset(assignment_id, reason="", changed_by="admin"):
    conn = get_conn()
    if USE_PG:
        cur = conn.cursor(); cur.execute("SELECT * FROM assignments WHERE id=%s",(assignment_id,))
        asgn = _fetchone(cur)
    else:
        r = conn.execute("SELECT * FROM assignments WHERE id=?",(assignment_id,)).fetchone()
        asgn = dict(r) if r else None
    if not asgn: conn.close(); return False, "Tayinlash topilmadi"
    if USE_PG:
        cur = conn.cursor()
        cur.execute("UPDATE assignments SET is_active=0,returned_at=NOW() WHERE id=%s",(assignment_id,))
        cur.execute("UPDATE assets SET status='REGISTERED',updated_at=NOW() WHERE id=%s",(asgn["asset_id"],))
        cur.execute("INSERT INTO asset_history (asset_id,action,old_status,new_status,changed_by,reason) VALUES (%s,%s,%s,%s,%s,%s)",
                    (asgn["asset_id"],"RETURNED","ASSIGNED","REGISTERED",changed_by,reason))
    else:
        conn.execute("UPDATE assignments SET is_active=0,returned_at=datetime('now') WHERE id=?",(assignment_id,))
        conn.execute("UPDATE assets SET status='REGISTERED',updated_at=datetime('now') WHERE id=?",(asgn["asset_id"],))
        conn.execute("INSERT INTO asset_history (asset_id,action,old_status,new_status,changed_by,reason) VALUES (?,?,?,?,?,?)",
                     (asgn["asset_id"],"RETURNED","ASSIGNED","REGISTERED",changed_by,reason))
    conn.commit(); conn.close()
    return True, "Aktiv qaytarildi!"

# ─── ANALYTICS ─────────────────────────────────────────────
def get_stats():
    conn = get_conn()
    if USE_PG:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM assets"); total = cur.fetchone()[0]
        cur.execute("SELECT status,COUNT(*) FROM assets GROUP BY status")
        by_status = {r[0]:r[1] for r in cur.fetchall()}
        cur.execute("SELECT category,COUNT(*) FROM assets GROUP BY category")
        by_category = {r[0]:r[1] for r in cur.fetchall()}
        cur.execute("SELECT department,COUNT(*) FROM assignments WHERE is_active=1 AND department!='' GROUP BY department")
        by_dept = {r[0]:r[1] for r in cur.fetchall() if r[0]}
        cur.execute("SELECT COUNT(*) FROM asset_history WHERE created_at>=NOW()-INTERVAL '7 days'")
        recent = cur.fetchone()[0]
    else:
        total = conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
        by_status = dict(conn.execute("SELECT status,COUNT(*) FROM assets GROUP BY status").fetchall())
        by_category = dict(conn.execute("SELECT category,COUNT(*) FROM assets GROUP BY category").fetchall())
        by_dept = dict(conn.execute("SELECT department,COUNT(*) FROM assignments WHERE is_active=1 AND department!='' GROUP BY department").fetchall())
        recent = conn.execute("SELECT COUNT(*) FROM asset_history WHERE created_at>=datetime('now','-7 days')").fetchone()[0]
    conn.close()
    return {"total":total,"by_status":by_status,"by_category":by_category,"by_dept":by_dept,"recent":recent}

def get_all_history(limit=50):
    conn = get_conn()
    if USE_PG:
        cur = conn.cursor()
        cur.execute("SELECT h.*,a.name as asset_name FROM asset_history h JOIN assets a ON h.asset_id=a.id ORDER BY h.created_at DESC LIMIT %s",(limit,))
        rows = _fetchall(cur); conn.close(); return rows
    else:
        rows = conn.execute("SELECT h.*,a.name as asset_name FROM asset_history h JOIN assets a ON h.asset_id=a.id ORDER BY h.created_at DESC LIMIT ?",(limit,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

def is_db_empty():
    conn = get_conn()
    if USE_PG:
        cur = conn.cursor(); cur.execute("SELECT COUNT(*) FROM assets")
        count = cur.fetchone()[0]
    else:
        count = conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
    conn.close(); return count == 0
