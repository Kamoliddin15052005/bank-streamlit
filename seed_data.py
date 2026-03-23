"""Demo ma'lumotlar: python seed_data.py"""
from database import init_db, get_conn
import sqlite3

def seed():
    init_db()
    conn = get_conn()

    # Tozalash
    for t in ["asset_history","assignments","assets","employees"]:
        conn.execute(f"DELETE FROM {t}")
    conn.commit()

    print("👥 Xodimlar...")
    emps = [
        ("Alisher Karimov",   "EMP-001","IT",                "Toshkent filiali","a.karimov@bank.uz","+998901111111"),
        ("Zulfiya Rahimova",  "EMP-002","Moliya",            "Toshkent filiali","z.rahimova@bank.uz","+998902222222"),
        ("Bobur Yusupov",     "EMP-003","Buxgalteriya",      "Samarqand filiali","b.yusupov@bank.uz","+998903333333"),
        ("Nilufar Hasanova",  "EMP-004","HR",                "Toshkent filiali","n.hasanova@bank.uz","+998904444444"),
        ("Sherzod Mirzayev",  "EMP-005","Xavfsizlik",        "Buxoro filiali","sh.mirzayev@bank.uz","+998905555555"),
        ("Dilnoza Tosheva",   "EMP-006","Mijozlar xizmati",  "Toshkent filiali","d.tosheva@bank.uz","+998906666666"),
    ]
    for e in emps:
        conn.execute("INSERT INTO employees (full_name,employee_id,department,branch,email,phone) VALUES (?,?,?,?,?,?)", e)
    conn.commit()
    print(f"  ✅ {len(emps)} xodim")

    print("💻 Aktivlar...")
    assets = [
        ("Dell Laptop XPS 15",       "Laptop",    "IT",       "SN-LAP-001","Intel Core i7, 16GB RAM","ASSIGNED"),
        ("HP EliteBook 840",          "Laptop",    "IT",       "SN-LAP-002","Intel Core i5, 8GB RAM", "ASSIGNED"),
        ("Lenovo ThinkPad E15",       "Laptop",    "IT",       "SN-LAP-003","AMD Ryzen 5, 8GB RAM",   "REGISTERED"),
        ("Dell Monitor 24\"",         "Monitor",   "IT",       "SN-MON-001","Full HD, IPS panel",     "ASSIGNED"),
        ("HP LaserJet Pro",           "Printer",   "IT",       "SN-PRT-001","Monoxrom, A4",           "ASSIGNED"),
        ("Cisco Switch 24port",       "Switch",    "IT",       "SN-NET-001","24 port, Gigabit",       "ASSIGNED"),
        ("UPS APC 1500VA",            "UPS",       "IT",       "SN-UPS-001","1500VA, 230V",           "REGISTERED"),
        ("Server Dell PowerEdge R740","Server",    "IT",       "SN-SRV-001","2x Xeon, 64GB RAM",     "ASSIGNED"),
        ("Proyektor Epson EB-X51",    "Proyektor", "OFFICE",   "SN-PRJ-001","3600 lumen, HDMI",      "REGISTERED"),
        ("IP Telefon Yealink T42S",   "IP Telefon","OFFICE",   "SN-TEL-001","2 liniya, SIP",         "ASSIGNED"),
        ("IP Kamera Hikvision 4MP",   "Kamera",    "SECURITY", "SN-CAM-001","Kecha-kunduz, IP67",    "ASSIGNED"),
        ("Kartali o'quvchi HID",      "SKUD",      "SECURITY", "SN-ACC-001","RFID 125kHz",           "ASSIGNED"),
        ("Ofis stoli L-shaklida",     "Mebel",     "FURNITURE","SN-FRN-001","120x80sm, qora",        "ASSIGNED"),
        ("HP Laptop (eski)",          "Laptop",    "IT",       "SN-OLD-001","Eskirgan, 2018 yil",    "IN_REPAIR"),
        ("Canon Printer MF445",       "Printer",   "IT",       "SN-PRT-002","Yo'qolgan",             "LOST"),
        ("UPS Powercom 600VA",        "UPS",       "IT",       "SN-UPS-OLD","Batareya ishlamaydi",   "WRITTEN_OFF"),
    ]
    for a in assets:
        conn.execute(
            "INSERT INTO assets (name,asset_type,category,serial_number,description,status) VALUES (?,?,?,?,?,?)", a
        )
    conn.commit()
    print(f"  ✅ {len(assets)} aktiv")

    # Tarix
    print("📋 Tarix...")
    rows = conn.execute("SELECT id,name,status FROM assets").fetchall()
    for r in rows:
        conn.execute(
            "INSERT INTO asset_history (asset_id,action,new_status,changed_by,details) VALUES (?,?,?,?,?)",
            (r[0], "CREATED", "REGISTERED", "admin", f"'{r[1]}' ro'yxatga olindi")
        )
        if r[2] == "ASSIGNED":
            conn.execute(
                "INSERT INTO asset_history (asset_id,action,old_status,new_status,changed_by) VALUES (?,?,?,?,?)",
                (r[0], "ASSIGNED", "REGISTERED", "ASSIGNED", "admin")
            )
        elif r[2] == "IN_REPAIR":
            conn.execute(
                "INSERT INTO asset_history (asset_id,action,old_status,new_status,changed_by,reason) VALUES (?,?,?,?,?,?)",
                (r[0], "STATUS_CHANGED","ASSIGNED","IN_REPAIR","admin","Ekrani singan")
            )
        elif r[2] == "LOST":
            conn.execute(
                "INSERT INTO asset_history (asset_id,action,old_status,new_status,changed_by,reason) VALUES (?,?,?,?,?,?)",
                (r[0], "STATUS_CHANGED","ASSIGNED","LOST","admin","Inventarizatsiyada topilmadi")
            )
        elif r[2] == "WRITTEN_OFF":
            conn.execute(
                "INSERT INTO asset_history (asset_id,action,old_status,new_status,changed_by,reason) VALUES (?,?,?,?,?,?)",
                (r[0], "STATUS_CHANGED","IN_REPAIR","WRITTEN_OFF","admin","Ta'mirlash mumkin emas")
            )
    conn.commit()

    # Tayinlashlar
    print("🔗 Tayinlashlar...")
    emp_ids = [r[0] for r in conn.execute("SELECT id FROM employees ORDER BY id").fetchall()]
    assigned_assets = conn.execute("SELECT id FROM assets WHERE status='ASSIGNED' ORDER BY id").fetchall()
    for i, (aid,) in enumerate(assigned_assets):
        emp_id = emp_ids[i % len(emp_ids)]
        conn.execute(
            "INSERT INTO assignments (asset_id,employee_id,department,is_active) VALUES (?,?,?,1)",
            (aid, emp_id, emps[i % len(emps)][2])
        )
    conn.commit()
    conn.close()

    print("\n" + "="*45)
    print("🎉 DEMO MA'LUMOTLAR YUKLANDI!")
    print("="*45)
    print(f"👥 Xodimlar: {len(emps)}")
    print(f"💻 Aktivlar: {len(assets)}")
    print("\n▶ Ishga tushirish:")
    print("  streamlit run app.py")

if __name__ == "__main__":
    seed()
