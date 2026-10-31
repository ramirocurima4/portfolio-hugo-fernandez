"""
Smoke test del motor: verifica que TODAS las rutas Flask sigan registradas y respondiendo,
que el panel /admin siga protegido y que las vistas públicas rendericen sin errores Jinja.

Uso:  venv/bin/python tools/smoke_test.py [--dump-routes ruta.json] [--compare-routes ruta.json]
No escribe en la base de datos de producción: trabaja sobre una copia temporal de carnaval.db.
"""
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

# Copia temporal de la BD para no ensuciar datos reales (visitas, etc.)
tmpdir = tempfile.mkdtemp()
shutil.copy(os.path.join(ROOT, "carnaval.db"), os.path.join(tmpdir, "carnaval.db"))

import database  # noqa: E402

for attr in ("DB_PATH", "DATABASE", "DB_NAME"):
    if hasattr(database, attr):
        setattr(database, attr, os.path.join(tmpdir, "carnaval.db"))

import app as motor  # noqa: E402

app = motor.app
app.testing = True

args = sys.argv[1:]
rules = sorted(
    f"{','.join(sorted(r.methods - {'HEAD', 'OPTIONS'}))} {r.rule}" for r in app.url_map.iter_rules()
)
if "--dump-routes" in args:
    with open(args[args.index("--dump-routes") + 1], "w") as fh:
        json.dump(rules, fh, indent=1)
    print(f"[ok] {len(rules)} reglas volcadas")

failures = []


def check(name, cond, extra=""):
    print(("  PASS " if cond else "  FAIL ") + name + (f"  {extra}" if extra else ""))
    if not cond:
        failures.append(name)


if "--compare-routes" in args:
    with open(args[args.index("--compare-routes") + 1]) as fh:
        before = set(json.load(fh))
    missing = before - set(rules)
    check("ninguna ruta eliminada", not missing, f"faltan: {sorted(missing)}")

c = app.test_client()
print("\n== Vistas públicas ==")
for path in ["/", "/trajes", "/trajes?genero=Femenino", "/destaques", "/obras-maestras", "/coordinacion",
             "/comparsas", "/comparsa/Sapucay", "/entrevistas", "/materiales", "/comunidad/subir",
             "/login", "/traje/1", "/pages/trajes.html", "/api/trajes", "/api/trajes/obras-maestras"]:
    r = c.get(path)
    check(f"GET {path}", r.status_code in (200, 404) and r.status_code != 500, f"-> {r.status_code}")

print("\n== Protección de admin ==")
r = c.get("/admin")
check("/admin sin sesión redirige a login", r.status_code in (301, 302) and "login" in r.headers.get("Location", ""))
check("POST /api/trajes sin sesión es rechazado", c.post("/api/trajes", data={}).status_code in (401, 403))

print("\n== Filtración de archivos sensibles ==")
for sensitive in ["/.env", "/llave-google.json", "/carnaval.db", "/app.py", "/database.py", "/seed.py",
                  "/requirements.txt", "/.envS", "/memory.md", "/.git/config", "/static/../app.py"]:
    r = c.get(sensitive)
    check(f"{sensitive} NO accesible", r.status_code in (403, 404), f"-> {r.status_code}")

print("\n== Admin autenticado ==")
pwd = os.getenv("ADMIN_PASSWORD", "Panambi2027")
r = c.post("/login", data={"password": pwd}, follow_redirects=False)
check("login correcto", r.status_code in (301, 302))
r = c.get("/admin")
check("GET /admin 200 autenticado", r.status_code == 200, f"-> {r.status_code}")
body = r.get_data(as_text=True)
for hook in ["form-traje-cms", "tbody-trajes-admin", "tabla-moderacion-pendientes", "form-nueva-entrevista",
             "modal-editar-traje", "input-fotos-multiple", "chartComparsas", "btn-limpiar-errores"]:
    check(f"admin contiene #{hook}", hook in body)
r = c.get("/admin/editar/1")
check("GET /admin/editar/1", r.status_code in (200, 404), f"-> {r.status_code}")

print("\n== Límites de subida intactos ==")
check("MAX_CONTENT_LENGTH = 120MB", app.config.get("MAX_CONTENT_LENGTH") == 120 * 1024 * 1024)
src = open(os.path.join(ROOT, "app.py"), encoding="utf-8").read()
check("tope 6 archivos presente", "len(archivos_lista) > 6" in src and "archivos_lista[:6]" in src)
check("tope 20MB presente", "MAX_BYTES_POR_ARCHIVO = 20 * 1024 * 1024" in src)
check("integración Google Drive presente", "subir_a_google_drive" in src and "MediaIoBaseUpload" in src)

print("\n== Cabeceras ==")
r = c.get("/")
check("X-Content-Type-Options", r.headers.get("X-Content-Type-Options") == "nosniff")

shutil.rmtree(tmpdir, ignore_errors=True)
print(f"\n{'TODO OK' if not failures else 'FALLOS: ' + str(len(failures))}")
sys.exit(1 if failures else 0)
