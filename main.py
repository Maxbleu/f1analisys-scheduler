import json
import fastf1
import asyncio
import logging
import requests
import traceback
from posts import get_promt
from fastapi import FastAPI
from typing import Any, Dict
from utils import get_full_path, get_session, get_first_gp_date
from storage import AnalysisJsonStorage, SessionsAnalisysJsonStorage
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger("uvicorn")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger.info("⚙️F1Analisys-Scheduler se ha iniciado")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        loop = asyncio.get_running_loop()
        scheduler = AsyncIOScheduler(event_loop=loop)
        scheduler.start()
        app.state.scheduler = scheduler 

        session_analisys = sessions_analisys_json_storage.load()
        schedule_all_sessions(scheduler, session_analisys)
        schedule_next_year(scheduler, session_analisys)

        yield

    except Exception as e:
        print("ERROR en lifespan:", e)
        traceback.print_exc()
        raise e
    finally:
        scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
sessions_analisys_json_storage = SessionsAnalisysJsonStorage()
analisys_json_storage = AnalysisJsonStorage()
API_ANALYSIS_URL = "https://f1analisys-production.up.railway.app"

# Obtener imagen del servidor f1analisys
async def fetch_and_store_analysis(job_id: str, type_event: str, year: int, event: int, session: str, analises: dict):
    try:
        obj_session = get_session(type_event, year, event, session)
        for analisys in analises:
            url = API_ANALYSIS_URL+"/api"+get_full_path(type_event, year, event, session, obj_session, analisys)+"?convert_to_bytes=True"
            response = requests.get(url)
            if response.status_code == 200:
                json = response.json()
                promt = get_promt(obj_session, analisys)
                storage = analisys_json_storage.load()
                if not storage:
                    storage.append({
                        "session_name": job_id,
                        "analises": [ {"image": json} ]
                    })
                else:
                    storage["analises"].append({"image": json})
                analisys_json_storage.save(storage)
                logger.info(f"[✓] Imagen guardada para {job_id}")
    except Exception as e:
        logger.error(f"[X] Error para {job_id}: {e}")

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
            logger.info(f"[🏎️] Programando el evento: {row['OfficialEventName']}")
            for n_session in range(1, n_sessions):
                try:
                    session_start = f1_event.get_session_date(n_session)
                    run_time = session_start + timedelta(hours=2)
                    session_name = f1_event.get_session_name(n_session)
                    analises = sessions_analisys[session_name]
                    scheduler.add_job(
                        fetch_and_store_analysis,
                        trigger="date",
                        run_date=run_time,
                        args=[session_name, type_event, year, event, session_name, analises],
                        id=session_name,
                        replace_existing=True
                    )
                    logger.info(f"[🕒] Programado {session_name} para {run_time}")
                except Exception as e:
                    logger.error(f"Error en sesión {n_session}: {e}")
        except Exception as e:
            logger.error(f"Error al obtener evento: {e}")

# Programa cargar todas las sesiones del año una semana antes del primer gp
def schedule_one_week_before(scheduler: AsyncIOScheduler, sessions_analisys: dict):
    year = datetime.now().year
    gp_date = get_first_gp_date(year)         # pandas.Timestamp
    run_date = gp_date - timedelta(weeks=1)
    print(f"[Debug] primer GP: {gp_date}, ejecútame en {run_date}")

    scheduler.add_job(
        schedule_all_sessions,
        trigger="date",
        run_date=run_date,
        args=[scheduler, sessions_analisys],
        id="schedule_all_sessions_before_first_gp",
        replace_existing=True
    )
    logger.info(f"[Scheduler] schedule_all_sessions programado para {run_date.isoformat()}")
    schedule_next_year(scheduler, sessions_analisys)

# Programar ejecutar una acción el primer día del siguiente año
def schedule_next_year(scheduler: AsyncIOScheduler, session_analisys: dict):

    next_year = datetime.now().year + 1
    target_date = datetime(next_year, 1, 1)
    scheduler.add_job(
        schedule_one_week_before,
        trigger="date",
        run_date=target_date,
        args=[scheduler, session_analisys],
        id="schedule_one_week_before",
        replace_existing=True
    )
    logger.info(f"[Scheduler] schedule_one_week_before programado para {target_date.isoformat()}")

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