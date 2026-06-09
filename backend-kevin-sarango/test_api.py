"""Suite de validaciones del API GeoGuard EUDR."""
import os, time, subprocess, sys, re, requests
from jose import jwt

BASE = "http://127.0.0.1:8031"
SECRET = "EUDR-Auth-2026-v1-xK9mPqRz2wL7nBv4Jd8Sf3Gh5Tq1Wx0Zy"
ALG = "HS256"

PASS = 0; FAIL = 0

def make_token(sub, role):
    return jwt.encode({"sub": sub, "role": role, "exp": int(time.time()) + 3600}, SECRET, algorithm=ALG)

ADM = make_token("admin@geoguard.ec", "ADMIN")
AUD = make_token("auditor@geoguard.ec", "AUDITOR")
CLI = make_token("cliente@geoguard.ec", "CLIENTE")

def H(token): return {"Authorization": f"Bearer {token}"}

def check(label, expected, actual):
    global PASS, FAIL
    ok = str(expected) == str(actual)
    symbol = "PASS" if ok else "FAIL"
    if ok:
        PASS += 1
        print(f"  {symbol}  {label}")
    else:
        FAIL += 1
        print(f"  {symbol}  {label}  (esperado={expected!r} actual={actual!r})")

def sc(resp): return resp.status_code
def j(resp): return resp.json()

# ── ARRANQUE ──────────────────────────────────────────────────
print("\n====== ARRANQUE ======")
check("GET / -> 200",      200, sc(requests.get(f"{BASE}/")))
check("GET /health -> 200",200, sc(requests.get(f"{BASE}/health")))

# ── AUTH ──────────────────────────────────────────────────────
print("\n====== AUTH ======")
check("Sin token -> 403",      403, sc(requests.get(f"{BASE}/api/v1/expedientes/")))
check("Token invalido -> 401", 401, sc(requests.get(f"{BASE}/api/v1/expedientes/", headers={"Authorization": "Bearer basura"})))

# ── ROLES ─────────────────────────────────────────────────────
print("\n====== ROLES ======")
# Limpiar rol previo si existe (aislamiento de tests)
roles_existentes = requests.get(f"{BASE}/api/v1/roles/", headers=H(ADM)).json()
for rol in roles_existentes:
    if rol.get("nombre") == "AUDITOR":
        requests.delete(f"{BASE}/api/v1/roles/{rol['id']}", headers=H(ADM))
r = requests.post(f"{BASE}/api/v1/roles/", json={"nombre": "AUDITOR", "descripcion": "Auditor GEE"}, headers=H(ADM))
check("POST rol (ADMIN) -> 201",   201, sc(r))
check("GET roles (ADMIN) -> 200",  200, sc(requests.get(f"{BASE}/api/v1/roles/", headers=H(ADM))))
check("POST rol (CLIENTE) -> 403", 403, sc(requests.post(f"{BASE}/api/v1/roles/", json={"nombre": "ADMIN"}, headers=H(CLI))))

# ── USUARIOS ─────────────────────────────────────────────────
print("\n====== USUARIOS ======")
# Email único por ejecución para evitar conflictos con soft-delete
test_email = f"test_{int(time.time())}@geoguard.ec"
u = requests.post(f"{BASE}/api/v1/usuarios/", json={"nombre": "Test Val", "email": test_email, "password": "Pass123!"}, headers=H(ADM))
check("POST usuario (ADMIN) -> 201",      201,  sc(u))
check("activo=True al crear",             True, j(u).get("activo"))
check("email duplicado -> 400",           400,  sc(requests.post(f"{BASE}/api/v1/usuarios/", json={"nombre": "Test Val", "email": test_email, "password": "Pass123!"}, headers=H(ADM))))
check("CLIENTE no puede listar -> 403",   403,  sc(requests.get(f"{BASE}/api/v1/usuarios/", headers=H(CLI))))
check("AUDITOR no puede crear -> 403",    403,  sc(requests.post(f"{BASE}/api/v1/usuarios/", json={"nombre":"X","email":"x@x.ec","password":"123"}, headers=H(AUD))))

# ── FINCAS ────────────────────────────────────────────────────
print("\n====== FINCAS ======")
f = requests.post(f"{BASE}/api/v1/fincas/", json={"nombre": "Finca Test", "provincia": "Loja", "area_total_ha": 3.5, "tenencia": "PROPIA"}, headers=H(ADM))
finca_id = j(f).get("id")
check("POST finca (ADMIN) -> 201",         201, sc(f))
check("GET finca (CLIENTE) -> 200",        200, sc(requests.get(f"{BASE}/api/v1/fincas/{finca_id}", headers=H(CLI))))
check("DELETE finca (CLIENTE) -> 403",     403, sc(requests.delete(f"{BASE}/api/v1/fincas/{finca_id}", headers=H(CLI))))

# ── EXPEDIENTES ───────────────────────────────────────────────
print("\n====== EXPEDIENTES ======")
e = requests.post(f"{BASE}/api/v1/expedientes/", json={
    "nombre_completo": "Maria Lopez", "cedula_id": "0102030405",
    "nombre_finca": "Finca Verde", "provincia": "Loja",
    "datos_agroambientales": {"indice_shannon": 2.1, "total_stock_carbono": 38.5}
}, headers=H(ADM))
exp_id = j(e).get("id")
check("POST expediente (ADMIN) -> 201",       201,       sc(e))
check("Estado inicial = PENDIENTE",           "PENDIENTE", j(e).get("estado"))
check("Historial inicial = 1 entrada",        1,         len(j(e).get("historial", [])))
check("Datos agroambientales = 1 registro",   1,         len(j(e).get("datos_agroambientales", [])))
check("GET expediente (CLIENTE) -> 200",      200,       sc(requests.get(f"{BASE}/api/v1/expedientes/{exp_id}", headers=H(CLI))))
check("POST expediente (CLIENTE) -> 403",     403,       sc(requests.post(f"{BASE}/api/v1/expedientes/", json={"nombre_completo":"x","cedula_id":"x","nombre_finca":"x"}, headers=H(CLI))))
check("GET expediente inexistente -> 404",    404,       sc(requests.get(f"{BASE}/api/v1/expedientes/no-existe", headers=H(ADM))))

# ── AUDITORIA GEE ────────────────────────────────────────────
print("\n====== AUDITORIA GEE ======")
a = requests.post(f"{BASE}/api/v1/auditoria/", json={
    "expediente_id": exp_id, "resultado": "APROBADO", "deforestacion_detectada": False
}, headers=H(AUD))
check("POST auditoria (AUDITOR) -> 201",              201,                  sc(a))
check("resultado = APROBADO",                         "APROBADO",           j(a).get("resultado"))
check("ejecutado_por = sub del token",                "auditor@geoguard.ec",j(a).get("ejecutado_por"))
exp_after = requests.get(f"{BASE}/api/v1/expedientes/{exp_id}", headers=H(ADM)).json()
check("Expediente estado -> APROBADO tras auditoria", "APROBADO",           exp_after.get("estado"))
check("Historial = 2 entradas tras auditoria",        2,                    len(exp_after.get("historial", [])))
check("GET auditorias expediente (CLIENTE) -> 200",   200,                  sc(requests.get(f"{BASE}/api/v1/auditoria/expediente/{exp_id}", headers=H(CLI))))
check("POST auditoria (CLIENTE) -> 403",              403,                  sc(requests.post(f"{BASE}/api/v1/auditoria/", json={"expediente_id":exp_id,"resultado":"APROBADO","deforestacion_detectada":False}, headers=H(CLI))))

# ── CERTIFICADOS DDS ─────────────────────────────────────────
print("\n====== CERTIFICADOS DDS ======")
c = requests.post(f"{BASE}/api/v1/certificados/", json={"expediente_id": exp_id}, headers=H(ADM))
cert_id = j(c).get("id")
check("POST certificado (ADMIN) -> 201",           201,                sc(c))
check("estado = VIGENTE",                          "VIGENTE",          j(c).get("estado"))
check("generado_por = sub del token ADMIN",        "admin@geoguard.ec",j(c).get("generado_por"))
codigo = j(c).get("codigo_certificado", "")
check("codigo formato DDS-YYYY-XXXXXXXX",          True, bool(re.match(r"DDS-\d{4}-[A-F0-9]{8}$", codigo)))
rev = requests.patch(f"{BASE}/api/v1/certificados/{cert_id}/revocar", headers=H(ADM))
check("PATCH revocar -> REVOCADO",                 "REVOCADO",         j(rev).get("estado"))
check("AUDITOR no puede revocar -> 403",           403,                sc(requests.patch(f"{BASE}/api/v1/certificados/{cert_id}/revocar", headers=H(AUD))))

# certificado sin auditoria aprobada
e2 = requests.post(f"{BASE}/api/v1/expedientes/", json={"nombre_completo":"Sin Auditoria","cedula_id":"8888888888","nombre_finca":"Vacia"}, headers=H(ADM))
exp2_id = j(e2).get("id")
check("Certificado sin audit APROBADA -> 400",     400,                sc(requests.post(f"{BASE}/api/v1/certificados/", json={"expediente_id": exp2_id}, headers=H(ADM))))

# ── AGROAMBIENTAL ────────────────────────────────────────────
print("\n====== AGROAMBIENTAL ======")
check("GET agroambiental (CLIENTE) -> 200",        200, sc(requests.get(f"{BASE}/api/v1/agroambiental/{exp_id}", headers=H(CLI))))
check("GET resumen carbono (AUDITOR) -> 200",      200, sc(requests.get(f"{BASE}/api/v1/agroambiental/resumen/carbono", headers=H(AUD))))
check("POST agroambiental (CLIENTE) -> 403",       403, sc(requests.post(f"{BASE}/api/v1/agroambiental/{exp_id}", json={}, headers=H(CLI))))

print(f"\n{'='*40}")
print(f"  TOTAL: {PASS + FAIL}  |  PASS: {PASS}  |  FAIL: {FAIL}")
print(f"{'='*40}")
sys.exit(0 if FAIL == 0 else 1)
