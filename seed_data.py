"""Demo ma'lumotlar: python seed_data.py"""
from database import init_db, get_conn, USE_PG

def _exec(conn, cur, sql, params=()):
    if USE_PG:
        cur.execute(sql.replace("?", "%s"), params)
    else:
        conn.execute(sql, params)

def _fetchall(conn, cur, sql, params=()):
    if USE_PG:
        cur.execute(sql.replace("?", "%s"), params)
        return [dict(r) for r in cur.fetchall()]
    else:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

def seed():
    init_db()
    conn = get_conn()
    cur = conn.cursor() if USE_PG else None

    for t in ["asset_history", "assignments", "assets", "employees"]:
        _exec(conn, cur, f"DELETE FROM {t}")
    conn.commit()

    print("👥 Xodimlar...")
    emps = [
        ("Alisher Karimov",  "EMP-001", "IT",               "Toshkent filiali",  "a.karimov@bank.uz",   "+998901111111"),
        ("Zulfiya Rahimova", "EMP-002", "Moliya",            "Toshkent filiali",  "z.rahimova@bank.uz",  "+998902222222"),
        ("Bobur Yusupov",    "EMP-003", "Buxgalteriya",      "Samarqand filiali", "b.yusupov@bank.uz",   "+998903333333"),
        ("Nilufar Hasanova", "EMP-004", "HR",                "Toshkent filiali",  "n.hasanova@bank.uz",  "+998904444444"),
        ("Sherzod Mirzayev", "EMP-005", "Xavfsizlik",        "Buxoro filiali",    "sh.mirzayev@bank.uz", "+998905555555"),
        ("Dilnoza Tosheva",  "EMP-006", "Mijozlar xizmati",  "Toshkent filiali",  "d.tosheva@bank.uz",   "+998906666666"),
    ]
    for e in emps:
        _exec(conn, cur,
            "INSERT INTO employees (full_name,employee_id,department,branch,email,phone) VALUES (?,?,?,?,?,?)", e)
    conn.commit()
    print(f"  ✅ {len(emps)} xodim")

    print("💻 Aktivlar...")
    assets = [
        ("Dell Laptop XPS 15",        "Laptop",     "IT",        "SN-LAP-001", "Intel Core i7, 16GB RAM", "ASSIGNED"),
        ("HP EliteBook 840",           "Laptop",     "IT",        "SN-LAP-002", "Intel Core i5, 8GB RAM",  "ASSIGNED"),
        ("Lenovo ThinkPad E15",        "Laptop",     "IT",        "SN-LAP-003", "AMD Ryzen 5, 8GB RAM",    "REGISTERED"),
        ("Dell Monitor 24\"",          "Monitor",    "IT",        "SN-MON-001", "Full HD, IPS panel",      "ASSIGNED"),
        ("HP LaserJet Pro",            "Printer",    "IT",        "SN-PRT-001", "Monoxrom, A4",            "ASSIGNED"),
        ("Cisco Switch 24port",        "Switch",     "IT",        "SN-NET-001", "24 port, Gigabit",        "ASSIGNED"),
        ("UPS APC 1500VA",             "UPS",        "IT",        "SN-UPS-001", "1500VA, 230V",            "REGISTERED"),
        ("Server Dell PowerEdge R740", "Server",     "IT",        "SN-SRV-001", "2x Xeon, 64GB RAM",      "ASSIGNED"),
        ("Proyektor Epson EB-X51",     "Proyektor",  "OFFICE",    "SN-PRJ-001", "3600 lumen, HDMI",       "REGISTERED"),
        ("IP Telefon Yealink T42S",    "IP Telefon", "OFFICE",    "SN-TEL-001", "2 liniya, SIP",           "ASSIGNED"),
        ("IP Kamera Hikvision 4MP",    "Kamera",     "SECURITY",  "SN-CAM-001", "Kecha-kunduz, IP67",     "ASSIGNED"),
        ("Kartali o'quvchi HID",       "SKUD",       "SECURITY",  "SN-ACC-001", "RFID 125kHz",             "ASSIGNED"),
        ("Ofis stoli L-shaklida",      "Mebel",      "FURNITURE", "SN-FRN-001", "120x80sm, qora",         "ASSIGNED"),
        ("HP Laptop (eski)",           "Laptop",     "IT",        "SN-OLD-001", "Eskirgan, 2018 yil",     "IN_REPAIR"),
        ("Canon Printer MF445",        "Printer",    "IT",        "SN-PRT-002", "Yo'qolgan",               "LOST"),
        ("UPS Powercom 600VA",         "UPS",        "IT",        "SN-UPS-OLD", "Batareya ishlamaydi",    "WRITTEN_OFF"),
    ]
    for a in assets:
        _exec(conn, cur,
            "INSERT INTO assets (name,asset_type,category,serial_number,description,status) VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    print(f"  ✅ {len(assets)} aktiv")

    print("📋 Tarix...")
    rows = _fetchall(conn, cur, "SELECT id,name,status FROM assets")
    for r in rows:
        _exec(conn, cur,
            "INSERT INTO asset_history (asset_id,action,new_status,changed_by,details) VALUES (?,?,?,?,?)",
            (r["id"], "CREATED", "REGISTERED", "admin", f"'{r['name']}' ro'yxatga olindi"))
        if r["status"] == "ASSIGNED":
            _exec(conn, cur,
                "INSERT INTO asset_history (asset_id,action,old_status,new_status,changed_by) VALUES (?,?,?,?,?)",
                (r["id"], "ASSIGNED", "REGISTERED", "ASSIGNED", "admin"))
        elif r["status"] == "IN_REPAIR":
            _exec(conn, cur,
                "INSERT INTO asset_history (asset_id,action,old_status,new_status,changed_by,reason) VALUES (?,?,?,?,?,?)",
                (r["id"], "STATUS_CHANGED", "ASSIGNED", "IN_REPAIR", "admin", "Ekrani singan"))
        elif r["status"] == "LOST":
            _exec(conn, cur,
                "INSERT INTO asset_history (asset_id,action,old_status,new_status,changed_by,reason) VALUES (?,?,?,?,?,?)",
                (r["id"], "STATUS_CHANGED", "ASSIGNED", "LOST", "admin", "Inventarizatsiyada topilmadi"))
        elif r["status"] == "WRITTEN_OFF":
            _exec(conn, cur,
                "INSERT INTO asset_history (asset_id,action,old_status,new_status,changed_by,reason) VALUES (?,?,?,?,?,?)",
                (r["id"], "STATUS_CHANGED", "IN_REPAIR", "WRITTEN_OFF", "admin", "Ta'mirlash mumkin emas"))
    conn.commit()

    print("🔗 Tayinlashlar...")
    emp_rows = _fetchall(conn, cur, "SELECT id FROM employees ORDER BY id")
    emp_ids = [r["id"] for r in emp_rows]
    assigned_rows = _fetchall(conn, cur, "SELECT id FROM assets WHERE status='ASSIGNED' ORDER BY id")
    for i, r in enumerate(assigned_rows):
        _exec(conn, cur,
            "INSERT INTO assignments (asset_id,employee_id,department,is_active) VALUES (?,?,?,1)",
            (r["id"], emp_ids[i % len(emp_ids)], emps[i % len(emps)][2]))
    conn.commit()
    conn.close()

    print("\n" + "="*45)
    print("🎉 DEMO MA'LUMOTLAR YUKLANDI!")
    print("="*45)
    print(f"👥 Xodimlar: {len(emps)}")
    print(f"💻 Aktivlar: {len(assets)}")

if __name__ == "__main__":
    seed()