import subprocess
import sys
import os

def init_db():
    # Añadir el directorio Scripts del venv al PATH para que la CLI de Node
    # pueda encontrar el ejecutable prisma-client-py durante `generate`.
    venv_scripts = os.path.join(os.path.dirname(sys.executable))
    env = os.environ.copy()
    env["PATH"] = venv_scripts + os.pathsep + env.get("PATH", "")

    print("Generando cliente Prisma Python...")
    subprocess.run([sys.executable, "-m", "prisma", "generate"], check=True, env=env)

    print("Aplicando schema a la base de datos...")
    subprocess.run([sys.executable, "-m", "prisma", "db", "push"], check=True, env=env)

    print("Base de datos inicializada correctamente.")

if __name__ == "__main__":
    init_db()
