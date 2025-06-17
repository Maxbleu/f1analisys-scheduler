import os
import json
import fastf1
import asyncio
import requests
from utils import get_full_path
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()

    scheduler = AsyncIOScheduler(event_loop=loop)
    scheduler.start()
    app.state.scheduler = scheduler 

    session_analisys = load_sessions_f1analisys()
    schedule_all_sessions(scheduler, session_analisys)

    yield 

    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

SESSIONS_ANALISYS_FILE = "sessions_analisys.json"
ANALISYS_FILE = "analisys.json"
API_ANALYSIS_URL = "https://f1analisys-production.up.railway.app"

# Cargar almacenamiento de imágenes
def load_storage():
    if os.path.exists(ANALISYS_FILE):
        with open(ANALISYS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_storage(storage):
    with open(ANALISYS_FILE, "w") as f:
        json.dump(storage, f)

# Obtener los analisis de las sesiones
def load_sessions_f1analisys():
    with open(SESSIONS_ANALISYS_FILE, "r") as f:
        return json.load(f)

# Obtener imagen del servidor f1analisys
async def fetch_and_store_analysis(job_id, type_event, year, event, session, analises):
    try:
        for analisys in analises:
            url = API_ANALYSIS_URL+"/api"+get_full_path(type_event, year, event, session, analisys)+"?convert_to_bytes=True"
            response = requests.get(url)
            if response.status_code == 200:
                json = response.json()
                storage = load_storage()
                if not storage:
                    storage = {
                        job_id: {
                            analisys:json
                        }
                    }
                else:
                    storage.setdefault(job_id, {})[analisys] = json
                save_storage(storage)
                print(f"[✓] Imagen guardada para {job_id}")
    except Exception as e:
        print(f"[X] Error para {job_id}: {e}")

# Leer calendario y programar las tareas
def schedule_all_sessions(scheduler: AsyncIOScheduler, sessions_analisys):
    year = datetime.now().year
    events = fastf1.get_events_remaining()
    for _, row in events.iterrows():
        try:
            event = row["RoundNumber"]
            gp_event = fastf1.get_event(year, event)
            for n_session in range(1, 6):
                try:
                    session_start = gp_event.get_session_date(n_session)
                    run_time = session_start + timedelta(hours=2)
                    session_name = gp_event.get_session_name(n_session)
                    analises = sessions_analisys[session_name]
                    job_id = f"{event}_{session_name}"
                    type_event = "official"
                    scheduler.add_job(
                        fetch_and_store_analysis,
                        trigger="date",
                        run_date=run_time,
                        args=[job_id, type_event, year, event, session_name, analises],
                        id=job_id,
                        replace_existing=True
                    )
                    print(f"[🕒] Programado {session_name} para {run_time}")
                except Exception as e:
                    print(f"Error en sesión {n_session}: {e}")
        except Exception as e:
            print(f"Error al obtener evento: {e}")

# Endpoint para consultar una imagen por session_id
@app.get("/images/{session_id}")
def get_image(session_id: str):
    storage = load_storage()
    if session_id not in storage:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    return {"session_id": session_id, "image_base64": storage[session_id]}