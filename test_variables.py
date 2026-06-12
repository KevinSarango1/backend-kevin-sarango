import time, requests
from jose import jwt

BASE = "http://127.0.0.1:8035"
SECRET = "EUDR-Auth-2026-v1-xK9mPqRz2wL7nBv4Jd8Sf3Gh5Tq1Wx0Zy"
ADM = jwt.encode({"sub": "admin@geoguard.ec", "role": "SUPER_ADMIN", "exp": int(time.time())+3600}, SECRET, algorithm="HS256")
H = {"Authorization": f"Bearer {ADM}"}

# 1. Crear expediente
e = requests.post(f"{BASE}/api/v1/expedientes/", json={
    "nombre_completo": "Carlos Prueba",
    "cedula_id": "9999999999",
    "nombre_finca": "Finca Variables"
}, headers=H).json()
exp_id = e["id"]
print(f"[1] Expediente creado: {exp_id}")

# 2. Registrar datos agroambientales CON variables dinamicas
r = requests.post(f"{BASE}/api/v1/agroambiental/{exp_id}", json={
    "indice_shannon": 2.1,
    "indice_simpson": 0.85,
    "total_stock_carbono": 38.5,
    "variables": [
        {"nombre": "pH del suelo",      "valor": "6.5",          "tipo_dato": "FLOAT"},
        {"nombre": "Humedad relativa",  "valor": "75",            "tipo_dato": "INTEGER"},
        {"nombre": "Tipo de cobertura", "valor": "Bosque nativo", "tipo_dato": "STRING"}
    ]
}, headers=H)

print(f"\n[2] POST agroambiental -> Status: {r.status_code}")
dato = r.json()
print(f"    Dato ID:             {dato['id']}")
print(f"    indice_shannon:      {dato['indice_shannon']}")
print(f"    total_stock_carbono: {dato['total_stock_carbono']}")
print(f"    Variables creadas:   {len(dato['variables'])}")
for v in dato["variables"]:
    print(f"      - [{v['tipo_dato']}] {v['nombre']} = {v['valor']}")

# 3. GET confirma que las variables vienen incluidas
g = requests.get(f"{BASE}/api/v1/agroambiental/{exp_id}", headers=H).json()
print(f"\n[3] GET agroambiental -> variables en respuesta: {len(g[0]['variables'])}")

# 4. Sin variables (campo opcional)
r2 = requests.post(f"{BASE}/api/v1/agroambiental/{exp_id}", json={
    "indice_shannon": 1.5,
    "total_stock_carbono": 20.0
}, headers=H)
print(f"\n[4] POST sin variables -> Status: {r2.status_code}, variables: {len(r2.json()['variables'])}")
