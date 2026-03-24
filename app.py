import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import base64

from database import (
    init_db, is_db_empty,
    get_assets, get_asset, create_asset, update_asset, delete_asset,
    change_status, get_asset_history, get_employees, create_employee,
    delete_employee, get_assignments, assign_asset, return_asset,
    get_stats, get_all_history,
    ALLOWED, STATUS_UZ, STATUS_COLORS, CATEGORIES, DEPARTMENTS
)
from utils import generate_qr, ai_recommend_category, ai_risk_analysis

# ─── PAGE CONFIG ───────────────────────────────────────────
st.set_page_config(
    page_title="Bank Asset Management",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a3a6e 0%, #0f2347 100%);
        min-width: 220px !important;
    }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stRadio label {
        color: rgba(255,255,255,0.85) !important;
        font-size: 15px;
        padding: 6px 0;
    }
    [data-testid="stSidebar"] .stRadio label:hover { color: #f5c15e !important; }
    /* Sidebar toggle button */
    [data-testid="collapsedControl"] {
        background: #1a3a6e !important;
        color: white !important;
    }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px 24px;
        border-left: 5px solid #1a3a6e;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 8px;
    }
    .metric-card.green { border-left-color: #38a169; }
    .metric-card.yellow { border-left-color: #d69e2e; }
    .metric-card.red { border-left-color: #e53e3e; }
    .metric-card.blue { border-left-color: #3182ce; }
    .metric-val { font-size: 36px; font-weight: 800; color: #1a202c; margin: 0; }
    .metric-lbl { font-size: 12px; color: #718096; text-transform: uppercase; letter-spacing: 1px; margin: 0; }
    .page-title { font-size: 26px; font-weight: 800; color: #1a3a6e; margin-bottom: 4px; }
    .page-sub { color: #718096; font-size: 14px; margin-bottom: 20px; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px; background: #f7fafc;
        border-radius: 10px; padding: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px; padding: 8px 20px; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ─── INIT + AUTO SEED ─────────────────────────────────────
init_db()

def _auto_seed():
    if is_db_empty():
        import seed_data
        seed_data.seed()

_auto_seed()

# ─── SIDEBAR ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏦 BankAsset")
    st.markdown("*Smart Office Platform*")
    st.divider()

    page = st.radio(
        "Menyu",
        ["📊 Dashboard", "💻 Aktivlar", "👥 Xodimlar", "🔗 Tayinlashlar", "📋 Audit Tarixi"],
        label_visibility="collapsed"
    )
    st.divider()

    # DB holati
    from database import USE_PG
    if USE_PG:
        st.success("🟢 Supabase ulangan")
    else:
        st.warning("🟡 SQLite (lokal)")

    st.markdown("""
    <div style='font-size:11px; color:rgba(255,255,255,0.4); margin-top:12px;'>
    Bank Asset Management<br>v2.0 · Streamlit
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# 📊 DASHBOARD
# ═══════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.markdown("<p class='page-title'>📊 Dashboard</p>", unsafe_allow_html=True)
    st.markdown("<p class='page-sub'>Bank aktivlari umumiy ko'rinishi</p>", unsafe_allow_html=True)

    stats = get_stats()

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class='metric-card'>
            <p class='metric-val'>{stats['total']}</p>
            <p class='metric-lbl'>Jami aktivlar</p></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='metric-card green'>
            <p class='metric-val'>{stats['by_status'].get('ASSIGNED',0)}</p>
            <p class='metric-lbl'>🟢 Tayinlangan</p></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='metric-card yellow'>
            <p class='metric-val'>{stats['by_status'].get('IN_REPAIR',0)}</p>
            <p class='metric-lbl'>🟡 Ta'mirlashda</p></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class='metric-card red'>
            <p class='metric-val'>{stats['by_status'].get('LOST',0)}</p>
            <p class='metric-lbl'>🔴 Yo'qolgan</p></div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class='metric-card blue'>
            <p class='metric-val'>{stats['recent']}</p>
            <p class='metric-lbl'>📅 Haftalik amallar</p></div>""", unsafe_allow_html=True)

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Status bo'yicha taqsimot")
        if stats['by_status']:
            status_data = {STATUS_UZ.get(k,k): v for k,v in stats['by_status'].items()}
            color_map = {
                STATUS_UZ["REGISTERED"]: "#3182ce", STATUS_UZ["ASSIGNED"]: "#38a169",
                STATUS_UZ["IN_REPAIR"]: "#d69e2e", STATUS_UZ["LOST"]: "#e53e3e",
                STATUS_UZ["WRITTEN_OFF"]: "#718096",
            }
            fig = px.pie(values=list(status_data.values()), names=list(status_data.keys()),
                         color=list(status_data.keys()), color_discrete_map=color_map, hole=0.45)
            fig.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Ma'lumot yo'q")

    with col2:
        st.subheader("Kategoriya bo'yicha")
        if stats['by_category']:
            fig2 = px.bar(x=list(stats['by_category'].keys()), y=list(stats['by_category'].values()),
                          color=list(stats['by_category'].keys()),
                          color_discrete_sequence=px.colors.qualitative.Bold,
                          labels={"x":"Kategoriya","y":"Soni"})
            fig2.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Ma'lumot yo'q")

    if stats['by_dept']:
        st.subheader("Bo'lim bo'yicha faol tayinlashlar")
        fig3 = px.bar(x=list(stats['by_dept'].values()), y=list(stats['by_dept'].keys()),
                      orientation='h', color_discrete_sequence=["#1a3a6e"])
        fig3.update_layout(height=250, margin=dict(t=10,b=10,l=10,r=10))
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("🕐 So'nggi harakatlar")
    history = get_all_history(limit=8)
    if history:
        rows = [{"Harakat": h["action"],
                 "Aktiv": h.get("asset_name", f"#{h['asset_id']}"),
                 "Eski status": STATUS_UZ.get(h.get("old_status",""), "—"),
                 "Yangi status": STATUS_UZ.get(h.get("new_status",""), "—"),
                 "Kim": h["changed_by"],
                 "Sana": str(h["created_at"])[:16]} for h in history]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Harakatlar yo'q")

# ═══════════════════════════════════════════════════════════
# 💻 AKTIVLAR
# ═══════════════════════════════════════════════════════════
elif page == "💻 Aktivlar":
    st.markdown("<p class='page-title'>💻 Aktivlar</p>", unsafe_allow_html=True)
    st.markdown("<p class='page-sub'>Barcha bank aktivlari ro'yxati va boshqaruvi</p>", unsafe_allow_html=True)

    tabs = st.tabs(["📋 Ro'yxat", "➕ Qo'shish", "🔍 Ko'rish / QR"])

    with tabs[0]:
        fc1, fc2, fc3 = st.columns([3,1,1])
        with fc1:
            search = st.text_input("🔍 Qidirish", placeholder="Nomi, seriya raqami...", label_visibility="collapsed")
        with fc2:
            filter_status = st.selectbox("Status", ["Barchasi"]+list(STATUS_UZ.keys()), label_visibility="collapsed")
        with fc3:
            filter_cat = st.selectbox("Kategoriya", ["Barchasi"]+CATEGORIES, label_visibility="collapsed")

        assets = get_assets(
            search=search,
            status="" if filter_status=="Barchasi" else filter_status,
            category="" if filter_cat=="Barchasi" else filter_cat
        )
        if not assets:
            st.info("Aktivlar topilmadi")
        else:
            st.caption(f"Jami: {len(assets)} ta aktiv")
            for asset in assets:
                emoji = STATUS_COLORS.get(asset["status"], "⚪")
                with st.expander(f"{emoji} **{asset['name']}** — {asset['serial_number']} | {STATUS_UZ[asset['status']]}"):
                    c1, c2, c3 = st.columns([2,2,1])
                    with c1:
                        st.write(f"**Turi:** {asset['asset_type']}")
                        st.write(f"**Kategoriya:** `{asset['category']}`")
                        st.write(f"**Seriya:** `{asset['serial_number']}`")
                    with c2:
                        st.write(f"**Status:** {emoji} {STATUS_UZ[asset['status']]}")
                        st.write(f"**Tavsif:** {asset.get('description') or '—'}")
                        st.write(f"**Qo'shilgan:** {str(asset['created_at'])[:10]}")
                    with c3:
                        allowed_next = ALLOWED.get(asset["status"], [])
                        if allowed_next:
                            new_st = st.selectbox("Yangi status", allowed_next,
                                format_func=lambda x: STATUS_UZ[x], key=f"st_{asset['id']}")
                            reason = st.text_input("Sabab", key=f"rs_{asset['id']}", placeholder="ixtiyoriy")
                            if st.button("🔄 O'zgartir", key=f"chg_{asset['id']}", type="primary"):
                                ok, msg = change_status(asset["id"], new_st, reason)
                                if ok: st.success(msg); st.rerun()
                                else: st.error(msg)
                        if st.button("🗑 O'chirish", key=f"del_{asset['id']}"):
                            delete_asset(asset["id"]); st.success("O'chirildi!"); st.rerun()

    with tabs[1]:
        st.subheader("➕ Yangi aktiv qo'shish")
        with st.form("add_asset_form"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Nomi *", placeholder="Dell Laptop XPS 15")
                asset_type = st.text_input("Turi *", placeholder="Laptop")
                serial_number = st.text_input("Seriya raqami *", placeholder="SN-2024-001")
            with c2:
                category = st.selectbox("Kategoriya", CATEGORIES)
                description = st.text_area("Tavsif", placeholder="Aktiv haqida qisqacha...")

            col_ai, col_sub = st.columns([1,3])
            with col_ai:
                ai_cat = st.form_submit_button("🤖 AI Kategoriya", use_container_width=True)
            with col_sub:
                submitted = st.form_submit_button("💾 Saqlash", type="primary", use_container_width=True)

        if ai_cat and name:
            with st.spinner("AI tahlil qilmoqda..."):
                result = ai_recommend_category(name, asset_type, description)
            st.info(f"🤖 AI tavsiyasi: **{result['category']}** ({result.get('confidence','')}) — {result.get('reason','')}")

        if submitted:
            if not name or not asset_type or not serial_number:
                st.error("Barcha majburiy maydonlarni to'ldiring!")
            else:
                ok, msg = create_asset(name, asset_type, category, serial_number, description)
                if ok: st.success(msg); st.balloons()
                else: st.error(msg)

    with tabs[2]:
        st.subheader("🔍 Aktiv batafsil ko'rish")
        assets_list = get_assets()
        if not assets_list:
            st.info("Aktivlar yo'q")
        else:
            opts = {f"#{a['id']} — {a['name']} ({a['serial_number']})": a["id"] for a in assets_list}
            selected = st.selectbox("Aktivni tanlang", list(opts.keys()))
            asset_id = opts[selected]
            asset = get_asset(asset_id)
            history = get_asset_history(asset_id)

            if asset:
                col1, col2 = st.columns([3,2])
                with col1:
                    st.subheader(f"📋 {asset['name']}")
                    for label, val in [
                        ("Turi", asset["asset_type"]),
                        ("Kategoriya", asset["category"]),
                        ("Seriya", asset["serial_number"]),
                        ("Status", f"{STATUS_COLORS[asset['status']]} {STATUS_UZ[asset['status']]}"),
                        ("Tavsif", asset.get("description") or "—"),
                        ("Qo'shilgan", str(asset["created_at"])[:16]),
                    ]:
                        st.write(f"**{label}:** {val}")

                    with st.expander("✏️ Tahrirlash"):
                        with st.form(f"edit_{asset_id}"):
                            en = st.text_input("Nomi", value=asset["name"])
                            et = st.text_input("Turi", value=asset["asset_type"])
                            ec = st.selectbox("Kategoriya", CATEGORIES, index=CATEGORIES.index(asset["category"]))
                            ed = st.text_area("Tavsif", value=asset.get("description") or "")
                            if st.form_submit_button("Saqlash", type="primary"):
                                update_asset(asset_id, en, et, ec, ed)
                                st.success("Yangilandi!"); st.rerun()

                    if st.button("🤖 AI Risk tahlili", key="risk_btn"):
                        with st.spinner("Tahlil qilinmoqda..."):
                            risk = ai_risk_analysis(asset["name"], asset["status"], history)
                        level_color = {"LOW":"success","MEDIUM":"warning","HIGH":"error"}.get(risk["risk_level"],"info")
                        risk_emoji = {"LOW":"🟢","MEDIUM":"🟡","HIGH":"🔴"}.get(risk["risk_level"],"⚪")
                        getattr(st, level_color)(f"{risk_emoji} **Risk: {risk['risk_level']}** — {risk['recommendation']}")

                with col2:
                    st.subheader("📱 QR Kod")
                    active_asgn = [a for a in get_assignments(active_only=True) if a["asset_id"]==asset_id]
                    owner = active_asgn[0]["employee_name"] if active_asgn and active_asgn[0].get("employee_name") else "Tayinlanmagan"
                    qr_b64 = generate_qr(asset, owner)
                    st.image(base64.b64decode(qr_b64), caption=f"QR: {asset['serial_number']}", width=200)
                    st.download_button("⬇ QR yuklab olish", data=base64.b64decode(qr_b64),
                        file_name=f"qr_{asset['serial_number']}.png", mime="image/png", use_container_width=True)

                st.subheader("📋 Aktiv tarixi")
                if history:
                    hist_df = pd.DataFrame([{
                        "Harakat": h["action"],
                        "Eski": STATUS_UZ.get(h.get("old_status",""),"—"),
                        "Yangi": STATUS_UZ.get(h.get("new_status",""),"—"),
                        "Kim": h["changed_by"],
                        "Sabab": h.get("reason") or h.get("details") or "—",
                        "Sana": str(h["created_at"])[:16]
                    } for h in history])
                    st.dataframe(hist_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Tarix yo'q")

# ═══════════════════════════════════════════════════════════
# 👥 XODIMLAR
# ═══════════════════════════════════════════════════════════
elif page == "👥 Xodimlar":
    st.markdown("<p class='page-title'>👥 Xodimlar</p>", unsafe_allow_html=True)
    st.markdown("<p class='page-sub'>Bank xodimlari boshqaruvi</p>", unsafe_allow_html=True)

    tabs = st.tabs(["📋 Ro'yxat", "➕ Qo'shish"])

    with tabs[0]:
        employees = get_employees()
        if not employees:
            st.info("Xodimlar yo'q")
        else:
            st.caption(f"Jami: {len(employees)} ta xodim")
            df = pd.DataFrame([{
                "ID": f"#{e['id']}", "F.I.O": e["full_name"],
                "Xodim ID": e["employee_id"], "Bo'lim": e["department"],
                "Filial": e.get("branch") or "—", "Email": e.get("email") or "—",
                "Telefon": e.get("phone") or "—", "Qo'shilgan": str(e["created_at"])[:10]
            } for e in employees])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.divider()
            st.subheader("🗑 Xodimni o'chirish")
            del_opts = {f"{e['full_name']} ({e['employee_id']})": e["id"] for e in employees}
            del_sel = st.selectbox("Xodimni tanlang", list(del_opts.keys()))
            if st.button("O'chirish", type="secondary"):
                delete_employee(del_opts[del_sel]); st.success("O'chirildi!"); st.rerun()

    with tabs[1]:
        st.subheader("➕ Yangi xodim qo'shish")
        with st.form("add_emp_form"):
            c1, c2 = st.columns(2)
            with c1:
                fn = st.text_input("To'liq ismi *", placeholder="Alisher Karimov")
                eid = st.text_input("Xodim ID *", placeholder="EMP-001")
                dept = st.selectbox("Bo'lim *", DEPARTMENTS)
            with c2:
                branch = st.text_input("Filial", placeholder="Toshkent filiali")
                email = st.text_input("Email", placeholder="ali@bank.uz")
                phone = st.text_input("Telefon", placeholder="+998901234567")
            if st.form_submit_button("💾 Saqlash", type="primary", use_container_width=True):
                if not fn or not eid or not dept:
                    st.error("Majburiy maydonlarni to'ldiring!")
                else:
                    ok, msg = create_employee(fn, eid, dept, branch, email, phone)
                    if ok: st.success(msg); st.balloons()
                    else: st.error(msg)

# ═══════════════════════════════════════════════════════════
# 🔗 TAYINLASHLAR
# ═══════════════════════════════════════════════════════════
elif page == "🔗 Tayinlashlar":
    st.markdown("<p class='page-title'>🔗 Tayinlashlar</p>", unsafe_allow_html=True)
    st.markdown("<p class='page-sub'>Aktivlarni xodimlarga tayinlash va qaytarish</p>", unsafe_allow_html=True)

    tabs = st.tabs(["✅ Faol tayinlashlar", "📋 Barcha tayinlashlar", "➕ Tayinlash"])

    with tabs[0]:
        assignments = get_assignments(active_only=True)
        if not assignments:
            st.info("Faol tayinlashlar yo'q")
        else:
            for asgn in assignments:
                with st.expander(f"🔗 **{asgn['asset_name']}** → {asgn.get('employee_name') or 'Bo\'lim: '+asgn.get('department','—')}"):
                    c1, c2, c3 = st.columns([2,2,1])
                    with c1:
                        st.write(f"**Aktiv:** {asgn['asset_name']}")
                        st.write(f"**Seriya:** `{asgn['serial_number']}`")
                    with c2:
                        st.write(f"**Xodim:** {asgn.get('employee_name') or '—'}")
                        st.write(f"**Bo'lim:** {asgn.get('department') or asgn.get('emp_dept') or '—'}")
                        st.write(f"**Tayinlangan:** {str(asgn['assigned_at'])[:16]}")
                    with c3:
                        reason = st.text_input("Sabab", key=f"ret_r_{asgn['id']}", placeholder="ixtiyoriy")
                        if st.button("↩ Qaytarish", key=f"ret_{asgn['id']}", type="primary"):
                            ok, msg = return_asset(asgn["id"], reason)
                            if ok: st.success(msg); st.rerun()
                            else: st.error(msg)

    with tabs[1]:
        all_asgn = get_assignments(active_only=False)
        if all_asgn:
            df = pd.DataFrame([{
                "Aktiv": a["asset_name"], "Xodim": a.get("employee_name") or "—",
                "Bo'lim": a.get("department") or "—",
                "Tayinlangan": str(a["assigned_at"])[:16],
                "Qaytarilgan": str(a.get("returned_at",""))[:16] if a.get("returned_at") else "—",
                "Holat": "✅ Faol" if a["is_active"] else "↩ Qaytarilgan"
            } for a in all_asgn])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Tayinlashlar yo'q")

    with tabs[2]:
        st.subheader("➕ Aktiv tayinlash")
        available = get_assets(status="REGISTERED")
        employees = get_employees()
        if not available:
            st.warning("⚠️ REGISTERED statusidagi aktivlar yo'q")
        elif not employees:
            st.warning("⚠️ Avval xodim qo'shing")
        else:
            with st.form("assign_form"):
                asset_opts = {f"{a['name']} ({a['serial_number']})": a["id"] for a in available}
                emp_opts = {f"{e['full_name']} — {e['department']}": e["id"] for e in employees}
                emp_opts["— Bo'lim/Filiaga (xodim ko'rsatmasdan)"] = None
                sel_asset = st.selectbox("Aktiv *", list(asset_opts.keys()))
                sel_emp   = st.selectbox("Xodim", list(emp_opts.keys()))
                c1, c2 = st.columns(2)
                with c1: dept = st.selectbox("Bo'lim", [""]+DEPARTMENTS)
                with c2: branch = st.text_input("Filial", placeholder="Toshkent filiali")
                notes = st.text_area("Izoh", placeholder="Qo'shimcha ma'lumot...")
                if st.form_submit_button("🔗 Tayinlash", type="primary", use_container_width=True):
                    ok, msg = assign_asset(asset_id=asset_opts[sel_asset],
                        employee_id=emp_opts[sel_emp], department=dept,
                        branch=branch, notes=notes)
                    if ok: st.success(msg); st.balloons()
                    else: st.error(msg)

# ═══════════════════════════════════════════════════════════
# 📋 AUDIT TARIXI
# ═══════════════════════════════════════════════════════════
elif page == "📋 Audit Tarixi":
    st.markdown("<p class='page-title'>📋 Audit Tarixi</p>", unsafe_allow_html=True)
    st.markdown("<p class='page-sub'>Barcha amallarning to'liq audit logi</p>", unsafe_allow_html=True)

    limit = st.selectbox("Ko'rsatish soni", [20, 50, 100, 200], index=1)
    history = get_all_history(limit=limit)

    if not history:
        st.info("Tarix yo'q")
    else:
        ACTION_ICON = {"CREATED":"➕","ASSIGNED":"🔗","RETURNED":"↩","STATUS_CHANGED":"🔄","UPDATED":"✏️"}
        df = pd.DataFrame([{
            "#": h["id"],
            "Harakat": f"{ACTION_ICON.get(h['action'],'•')} {h['action']}",
            "Aktiv": h.get("asset_name", f"#{h['asset_id']}"),
            "Eski status": STATUS_UZ.get(h.get("old_status",""), "—"),
            "Yangi status": STATUS_UZ.get(h.get("new_status",""), "—"),
            "Kim": h["changed_by"],
            "Sabab": h.get("reason") or h.get("details") or "—",
            "Sana": str(h["created_at"])[:16]
        } for h in history])
        st.caption(f"Jami {len(history)} ta yozuv")
        st.dataframe(df, use_container_width=True, hide_index=True, height=500)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇ CSV yuklab olish", data=csv,
            file_name=f"audit_log_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
