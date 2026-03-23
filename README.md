# 🏦 Bank Asset Management — Streamlit

Smart Banking / Smart Office platformasi.

## ⚡ Ishga tushirish (2 qadam)

```bash
# 1. O'rnatish
pip install -r requirements.txt

# 2. Demo ma'lumotlar (ixtiyoriy)
python seed_data.py

# 3. Ishga tushirish
streamlit run app.py
```

Brauzerda: **http://localhost:8501**

## 🌐 Deploy (Render.com — bepul)

1. [render.com](https://render.com) → New → **Web Service**
2. GitLab repo URL ni kiriting
3. Sozlamalar:
   - **Runtime**: `Python 3`
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`

## ✅ Funksiyalar

| Funksiya | Holati |
|----------|--------|
| Aktiv CRUD + QR kod | ✅ |
| 5 holat + o'tish qoidalari | ✅ |
| Xodim boshqaruvi | ✅ |
| Tayinlash + qaytarish | ✅ |
| Audit log | ✅ |
| Dashboard + grafiklar | ✅ |
| AI kategoriya + risk | ✅ |
| CSV export | ✅ |
