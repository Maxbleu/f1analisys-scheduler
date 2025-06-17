import fastf1
from fastapi import HTTPException

def get_session(type_event, year, event, session):
    try:
        if type_event == "official":
                session = fastf1.get_session(year, event, session)
        elif type_event == "pretest":
            session = fastf1.get_testing_session(year, event, session)
        session.load()
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

def send_error_message(status_code, title, message):
    raise HTTPException(
        status_code= status_code,
        detail={
            "error": title,
            "message": message,
        }
    )