from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
import requests
import os
import secrets
import string
from groq import Groq

app = Flask(__name__)
CORS(app)

# === CONFIG ===
FRAUDSHIELD_URL = os.environ.get("FRAUDSHIELD_URL", "https://frauddetectionn.up.railway.app")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
VALID_API_KEYS = set(os.environ.get("VALID_API_KEYS", "").split(","))

groq_client = Groq(api_key=GROQ_API_KEY)

# === AUTH MIDDLEWARE ===
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-API-Key")
        if not key or key not in VALID_API_KEYS:
            return jsonify({
                "error": "Unauthorized",
                "message": "Invalid or missing API key. Include X-API-Key header."
            }), 401
        return f(*args, **kwargs)
    return decorated

# === GROQ EXPLANATION ===
def get_ai_explanation(prediction, probability, risk_level, amount, features):
    try:
        top_features = {k: round(v, 4) for k, v in list(features.items())[:10]}
        prompt = f"""Kamu adalah sistem AI untuk menjelaskan hasil deteksi fraud transaksi keuangan.

Data transaksi:
- Jumlah: Rp {amount:,.0f}
- Probabilitas Fraud: {probability*100:.1f}%
- Tingkat Risiko: {risk_level}
- Keputusan Model: {"FRAUD" if prediction == 1 else "AMAN"}
- Fitur PCA utama (V1-V10): {top_features}

Berikan penjelasan singkat (3-4 kalimat) dalam Bahasa Indonesia yang:
1. Menjelaskan kenapa transaksi ini {"dicurigai fraud" if prediction == 1 else "dianggap normal"}
2. Menyebutkan faktor utama yang mempengaruhi keputusan
3. Memberikan rekomendasi tindakan yang perlu diambil

Jawab langsung tanpa pembuka atau penutup."""

        chat = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.4
        )
        return chat.choices[0].message.content.strip()
    except Exception as e:
        return f"Penjelasan tidak tersedia: {str(e)}"

def get_recommendation(prediction, risk_level):
    recommendations = {
        (0, "LOW"): "Transaksi dapat diproses. Tidak ada tindakan tambahan diperlukan.",
        (0, "MEDIUM"): "Transaksi tampak aman namun tetap pantau aktivitas berikutnya.",
        (1, "MEDIUM"): "Tahan transaksi sementara dan lakukan verifikasi ke nasabah.",
        (1, "HIGH"): "Blokir transaksi segera dan eskalasi ke tim fraud investigasi.",
    }
    return recommendations.get((prediction, risk_level), "Lakukan review manual pada transaksi ini.")

# === ROUTES ===

@app.route("/")
def home():
    return jsonify({
        "name": "FraudShield API Wrapper",
        "version": "1.0.0",
        "author": "salman0812",
        "endpoints": {
            "POST /v1/analyze": "Analisis transaksi + AI explanation",
            "GET /v1/health": "Health check",
            "GET /v1/model/info": "Info model XGBoost",
            "POST /v1/keygen": "Generate API key baru (admin only)"
        }
    })

@app.route("/v1/health", methods=["GET"])
def health():
    try:
        r = requests.get(f"{FRAUDSHIELD_URL}/health", timeout=5)
        model_status = "online" if r.status_code == 200 else "degraded"
    except:
        model_status = "offline"

    return jsonify({
        "wrapper": "online",
        "model_backend": model_status,
        "groq": "connected" if GROQ_API_KEY else "not configured"
    })

@app.route("/v1/model/info", methods=["GET"])
@require_api_key
def model_info():
    try:
        r = requests.get(f"{FRAUDSHIELD_URL}/stats", timeout=5)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/v1/analyze", methods=["POST"])
@require_api_key
def analyze():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body kosong atau bukan JSON"}), 400

        # Forward ke FraudShield backend
        r = requests.post(
            f"{FRAUDSHIELD_URL}/predict/fraud",
            json=data,
            timeout=10
        )
        result = r.json()

        if "error" in result:
            return jsonify({"error": result["error"]}), 500

        prediction = result.get("prediction", 0)
        probability = result.get("probability", 0)
        risk_level = result.get("risk_level", "LOW")
        amount = data.get("Amount", 0)

        # AI Explanation via Groq
        explanation = get_ai_explanation(prediction, probability, risk_level, amount, data)
        recommendation = get_recommendation(prediction, risk_level)

        return jsonify({
            "status": "success",
            "result": {
                "prediction": "FRAUD" if prediction == 1 else "AMAN",
                "prediction_code": prediction,
                "probability": round(probability * 100, 2),
                "risk_level": risk_level,
                "alert": result.get("alert", False)
            },
            "ai_explanation": explanation,
            "recommendation": recommendation,
            "meta": {
                "model": "XGBoost",
                "backend": FRAUDSHIELD_URL,
                "explainer": "Groq llama-3.3-70b"
            }
        })

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Tidak bisa konek ke FraudShield backend"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/v1/keygen", methods=["POST"])
def keygen():
    # Simple admin auth untuk generate key baru
    admin_secret = request.headers.get("X-Admin-Secret")
    if admin_secret != os.environ.get("ADMIN_SECRET", ""):
        return jsonify({"error": "Forbidden"}), 403

    chars = string.ascii_letters + string.digits
    new_key = "fshield-" + "".join(secrets.choice(chars) for _ in range(32))
    return jsonify({
        "api_key": new_key,
        "note": "Tambahkan key ini ke VALID_API_KEYS environment variable di Railway"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
