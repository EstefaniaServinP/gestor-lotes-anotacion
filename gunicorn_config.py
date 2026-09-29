"""
Configuración de Gunicorn para el Gestor de Lotes de Anotación.
Valores por defecto pensados para un servidor de ~6 núcleos; ajustables por variables de entorno.
"""

import multiprocessing
import os

# WORKERS: núcleos - 2 (por defecto 4)
# Esto deja recursos para: sistema operativo, MongoDB, y otros procesos
workers = int(os.environ.get("GUNICORN_WORKERS", 4))

# WORKER CLASS: Sync workers (compatible con MongoDB)
worker_class = "sync"

# THREADS por worker: OPTIMIZADO para mejor concurrencia sin sobrecargar
# 3 threads por worker = 12 conexiones totales (4 workers x 3 threads)
threads = 3

# TIMEOUT: Aumentado para operaciones pesadas (sync-batch-files)
timeout = 120  # 2 minutos

# BINDING
bind = os.environ.get("BIND_ADDRESS", "0.0.0.0:5000")

# MEMORIA: Límite REDUCIDO para reciclar workers más frecuentemente (previene memory leaks)
max_requests = 500  # Recicla workers más seguido para liberar memoria
max_requests_jitter = 50  # Variación aleatoria para evitar restarts simultáneos

# LOGGING
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"

# PERFORMANCE
keepalive = 5  # Segundos para mantener conexiones keep-alive
worker_connections = 1000  # Conexiones simultáneas por worker

# GRACEFUL TIMEOUT
graceful_timeout = 30

# PRELOAD: DESACTIVADO para permitir inicialización correcta de MongoDB en cada worker
preload_app = False

# ESTADÍSTICAS
proc_name = "segmentacion_dashboard"

print(f"""
╔══════════════════════════════════════════════════════════╗
║  Gunicorn - Dashboard de Segmentación OPTIMIZADO        ║
╟──────────────────────────────────────────────────────────╢
║  Workers:              {workers}                          ║
║  Threads por worker:   {threads}                                    ║
║  Total capacidad:      {workers * threads} conexiones concurrentes      ║
║  Timeout:              {timeout}s                                ║
║  Bind:                 {bind}                      ║
║  Max requests:         {max_requests} (recicla workers)            ║
╚══════════════════════════════════════════════════════════╝
""")

def on_starting(server):
    """Hook al iniciar Gunicorn"""
    print("🚀 Iniciando Gunicorn con configuración optimizada...")

def worker_init(worker):
    """Hook al iniciar cada worker"""
    print(f"👷 Worker {worker.pid} iniciado")

def post_fork(server, worker):
    """Después de fork - inicializar MongoDB en cada worker"""
    from app import init_db
    print(f"🔧 Worker {worker.pid} - Inicializando MongoDB...")
    try:
        init_db()
        print(f"✅ Worker {worker.pid} - MongoDB inicializado correctamente")
    except Exception as e:
        print(f"⚠️ Worker {worker.pid} - Error inicializando MongoDB: {e}")
