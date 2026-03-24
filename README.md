# 🏦 Bank Asset Management System

Smart Banking / Smart Office — Bank aktivlarini markazlashtirilgan boshqarish platformasi.

## 🌐 Dastur manzili

**▶ [https://bank-app-nzamuscvmxbfuqc6cdfgfy.streamlit.app](https://bank-app-9ksdpxpxrtdhrqtgqyeg2f.streamlit.app/)**

> Brauzerda oching — hech narsa o'rnatish shart emas.

---

## ✅ Amalga oshirilgan funksiyalar

| Funksiya | Holati |
|----------|--------|
| Aktiv CRUD (qo'shish, tahrirlash, o'chirish) | ✅ |
| QR kod generatsiya | ✅ |
| 5 ta holat + o'tish qoidalari | ✅ |
| LOST aktiv qayta tayinlanmaydi | ✅ |
| Xodim boshqaruvi | ✅ |
| Tayinlash + qaytarish | ✅ |
| To'liq audit log | ✅ |
| Dashboard + grafiklar | ✅ |
| AI kategoriya tavsiyasi | ✅ |
| AI risk tahlili | ✅ |
| CSV export | ✅ |
| PostgreSQL (Supabase) | ✅ |

---

## 🔄 Holat diagrammasi

```
REGISTERED → ASSIGNED → IN_REPAIR → REGISTERED (loop)
    │             │            │
    │             ↓            ↓
    └──────→ WRITTEN_OFF ← LOST (terminal)
```

---

## ⚙️ Lokal ishlatish

```bash
pip install -r requirements.txt
python seed_data.py      # demo ma'lumotlar
streamlit run app.py     # http://localhost:8501
```

---

## 🛠 Texnologiyalar

| Qatlam | Texnologiya |
|--------|-------------|
| Frontend + Backend | Python Streamlit |
| Ma'lumotlar bazasi | Supabase PostgreSQL |
| Grafiklar | Plotly |
| QR kod | qrcode |
| AI | Anthropic Claude API |
| Hosting | Streamlit Community Cloud |
