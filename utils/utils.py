import fastf1
from fastapi import HTTPException
from datetime import datetime

def get_session(type_event, year, event, session):
    try:
        if type_event == "official":
                session = fastf1.get_session(year, event, session)
        elif type_event == "pretest":
            session = fastf1.get_testing_session(year, event, session)
        try:
            session.load()
        except Exception as load_error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load session data: {load_error}"
            )
    except Exception as e:
        send_error_message(
            status_code=404, 
            title="Selected session does not exist", 
            message=f'The session {year}/{event}/{session} does not exist or has not been loaded yet.'
        )
    return session

def get_laps(type_event, year, event, session):
    session = get_session(type_event, year, event, session)
    laps = session.laps
    return laps

def get_laps_from_session(session):
    laps = session.laps
    return laps

def get_first_gp_date(year=None):
    """
    Devuelve la fecha del primer Gran Premio de F1 de la temporada.
    """
    if year is None:
        year = datetime.now().year
    # Obtenemos el calendario de eventos (excluyendo test)
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    # La primera fila es el primer GP
    first_gp = schedule.iloc[0]
    # fastf1 devuelve un pandas.Timestamp
    return first_gp['Date']

def send_error_message(status_code, title, message):
    raise HTTPException(
        status_code= status_code,
        detail={
            "error": title,
            "message": message,
        }
    )