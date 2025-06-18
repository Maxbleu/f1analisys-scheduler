import json
import fastf1
import asyncio
import requests
from fastapi import FastAPI
from typing import Any, Dict
from utils import get_full_path
from storage import AnalysisJsonStorage, SessionsAnalisysJsonStorage
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()

    scheduler = AsyncIOScheduler(event_loop=loop)
    scheduler.start()
    app.state.scheduler = scheduler 

    session_analisys = sessions_analisys_json_storage.load()
    schedule_all_sessions(scheduler, session_analisys)

    yield 

    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
sessions_analisys_json_storage = SessionsAnalisysJsonStorage()
analisys_json_storage = AnalysisJsonStorage()
API_ANALYSIS_URL = "https://f1analisys-production.up.railway.app"

# Obtener imagen del servidor f1analisys
async def fetch_and_store_analysis(job_id: str, type_event: str, year: int, event: int, session: str, analises: dict):
    try:
        for analisys in analises:
            url = API_ANALYSIS_URL+"/api"+get_full_path(type_event, year, event, session, analisys)+"?convert_to_bytes=True"
            response = requests.get(url)
            if response.status_code == 200:
                json = response.json()
                storage = analisys_json_storage.load()
                if not storage:
                    storage = {
                        job_id: {
                            analisys:json
                        }
                    }
                else:
                    storage.setdefault(job_id, {})[analisys] = json
                analisys_json_storage.save(storage)
                print(f"[✓] Imagen guardada para {job_id}")
    except Exception as e:
        print(f"[X] Error para {job_id}: {e}")

# Leer calendario y programar las tareas
def schedule_all_sessions(scheduler: AsyncIOScheduler, sessions_analisys: dict):
    year = datetime.now().year
    events = fastf1.get_events_remaining()
    for _, row in events.iterrows():
        try:
            if row["EventFormat"] == "testing":
                n_sessions = 4
                type_event = "pretest"
                event = 1
                f1_event = fastf1.get_testing_event(year,event)
            else:
                n_sessions = 6
                type_event = "official"
                event = row["RoundNumber"]
                f1_event = fastf1.get_event(year, event)
            print("[🏎️] Programando el evento: ", row["OfficialEventName"])
            for n_session in range(1, n_sessions):
                try:
                    session_start = f1_event.get_session_date(n_session)
                    run_time = session_start + timedelta(hours=2)
                    session_name = f1_event.get_session_name(n_session)
                    analises = sessions_analisys[session_name]
                    job_id = f"{event}_{session_name}"
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

# Endpoint para obtener todas las sesiones
@app.get("/analises")
def get_analises():
    storage = analisys_json_storage.load()
    analisys_json_storage.save("")
    return storage

# Enpoint para obtener los analisis que se subirán en cada sesión
@app.get("/sessions_analisys")
def get_sessions_analisys():
    sessions_analisys = sessions_analisys_json_storage.load()
    return sessions_analisys

# Enpoint para actualizar el archivo de analisis que se subirán por sesión
@app.post("/update_sessions_analisys")
def update_sessions_analisys(sessions_analisys: Dict[str, Any]):
    sessions_analisys_json_storage.save(sessions_analisys)