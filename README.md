# FraudShield API Wrapper

API wrapper untuk FraudShield fraud detection model dengan AI explanation via Groq.

## Endpoints

| Method | Endpoint | Auth | Deskripsi |
|--------|----------|------|-----------|
| GET | `/` | - | Info API |
| GET | `/v1/health` | - | Health check |
| GET | `/v1/model/info` | X-API-Key | Info model XGBoost |
| POST | `/v1/analyze` | X-API-Key | Analisis transaksi |
| POST | `/v1/keygen` | X-Admin-Secret | Generate API key baru |

## Cara Pakai

### 1. Analisis Transaksi
```bash
curl -X POST https://YOUR-RAILWAY-URL/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: fshield-xxxxx" \
  -d '{
    "Time": 0,
    "Amount": 9800000,
    "V1": -1.35, "V2": -0.07, "V3": 2.53,
    "V4": 1.37, "V5": -0.33, "V6": 0.46,
    "V7": 0.23, "V8": 0.09, "V9": 0.36,
    "V10": 0.09, "V11": -0.55, "V12": -0.61,
    "V13": -0.99, "V14": -0.31, "V15": 0.08,
    "V16": -0.54, "V17": -1.06, "V18": -0.68,
    "V19": -0.23, "V20": -0.22, "V21": 0.1,
    "V22": 0.21, "V23": 0.16, "V24": 0.06,
    "V25": 0.02, "V26": 0.27, "V27": 0.14,
    "V28": 0.02
  }'
```

### 2. Generate API Key Baru
```bash
curl -X POST https://YOUR-RAILWAY-URL/v1/keygen \
  -H "X-Admin-Secret: PASSWORD_ADMIN_LO"
```

## Contoh Response `/v1/analyze`
```json
{
  "status": "success",
  "result": {
    "prediction": "FRAUD",
    "prediction_code": 1,
    "probability": 61.4,
    "risk_level": "MEDIUM",
    "alert": true
  },
  "ai_explanation": "Transaksi senilai Rp 9.800.000 ini dicurigai fraud karena...",
  "recommendation": "Tahan transaksi sementara dan lakukan verifikasi ke nasabah.",
  "meta": {
    "model": "XGBoost",
    "backend": "https://frauddetectionn.up.railway.app",
    "explainer": "Groq llama-3.3-70b"
  }
}
```

## Deploy ke Railway

1. Push repo ke GitHub
2. Connect ke Railway (akun baru lo)
3. Set environment variables dari `.env`
4. Deploy!

## Environment Variables

| Variable | Wajib | Keterangan |
|----------|-------|------------|
| GROQ_API_KEY | ✅ | API key dari console.groq.com |
| VALID_API_KEYS | ✅ | Key akses wrapper, pisah koma |
| ADMIN_SECRET | ✅ | Password untuk /v1/keygen |
| FRAUDSHIELD_URL | ✅ | URL backend FraudShield |
