import qrcode
import io
import base64
import os
import json
import httpx

def generate_qr(asset: dict, owner_name: str = "Tayinlanmagan") -> str:
    """Returns base64 PNG string of QR code."""
    text = (
        f"Aktiv: {asset['name']}\n"
        f"Seriya: {asset['serial_number']}\n"
        f"Kategoriya: {asset['category']}\n"
        f"Status: {asset['status']}\n"
        f"Egasi: {owner_name}"
    )
    qr = qrcode.QRCode(box_size=6, border=3)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def ai_recommend_category(name: str, asset_type: str, description: str = "") -> dict:
    """AI yoki rule-based kategoriya tavsiyasi."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    text = f"{name} {asset_type} {description}".lower()

    # Rule-based fallback
    def rule_based():
        if any(w in text for w in ["laptop", "kompyuter", "monitor", "printer", "server", "router", "switch", "ups", "pc", "telefon", "phone"]):
            return {"category": "IT", "confidence": "rule-based"}
        if any(w in text for w in ["stol", "kursiy", "shkaf", "desk", "chair", "mebel"]):
            return {"category": "FURNITURE", "confidence": "rule-based"}
        if any(w in text for w in ["kamera", "camera", "lock", "qulf", "xavfsizlik", "security", "skud"]):
            return {"category": "SECURITY", "confidence": "rule-based"}
        if any(w in text for w in ["qog'oz", "ruchka", "qalam", "printer", "ofis"]):
            return {"category": "OFFICE", "confidence": "rule-based"}
        return {"category": "OTHER", "confidence": "rule-based"}

    if not api_key:
        return rule_based()

    prompt = f"""Bank aktivini kategoriyalash. Faqat JSON qaytaring.
Kategoriyalar: IT, OFFICE, SECURITY, FURNITURE, OTHER

Aktiv: {name}
Turi: {asset_type}
Tavsif: {description}

Format: {{"category": "IT", "reason": "sabab"}}"""

    try:
        import httpx
        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 150,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=10.0
        )
        txt = r.json()["content"][0]["text"]
        parsed = json.loads(txt)
        return {"category": parsed.get("category", "OTHER"), "reason": parsed.get("reason", ""), "confidence": "AI"}
    except:
        return rule_based()

def ai_risk_analysis(asset_name: str, status: str, history: list) -> dict:
    """AI risk tahlili."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    repair_count = sum(1 for h in history if h.get("new_status") == "IN_REPAIR")
    lost_attempts = sum(1 for h in history if h.get("new_status") == "LOST")

    # Rule-based
    if status == "LOST":
        risk, msg = "HIGH", "Aktiv yo'qolgan — tezkor choralar ko'ring"
    elif status == "WRITTEN_OFF":
        risk, msg = "HIGH", "Aktiv hisobdan chiqarilgan"
    elif repair_count >= 2:
        risk, msg = "HIGH", f"Aktiv {repair_count} marta ta'mirlangan — almashtirish tavsiya etiladi"
    elif repair_count == 1:
        risk, msg = "MEDIUM", "Aktiv 1 marta ta'mirlangan — kuzatib boring"
    elif status == "IN_REPAIR":
        risk, msg = "MEDIUM", "Hozir ta'mirlashda"
    else:
        risk, msg = "LOW", "Aktiv yaxshi holatda"

    if not api_key:
        return {"risk_level": risk, "recommendation": msg, "source": "rule-based"}

    hist_summary = "; ".join([f"{h['action']}({h.get('new_status','')})" for h in history[:5]])
    prompt = f"""Bank IT aktivi risk tahlili. Faqat JSON qaytaring.

Aktiv: {asset_name}
Status: {status}
Tarix (oxirgi 5): {hist_summary}

Format: {{"risk_level": "LOW|MEDIUM|HIGH", "recommendation": "tavsiya (uzbek tilida)"}}"""

    try:
        import httpx
        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 200,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=10.0
        )
        txt = r.json()["content"][0]["text"]
        parsed = json.loads(txt)
        return {"risk_level": parsed.get("risk_level", risk), "recommendation": parsed.get("recommendation", msg), "source": "AI"}
    except:
        return {"risk_level": risk, "recommendation": msg, "source": "rule-based"}
