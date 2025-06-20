import fastf1
from fastf1.core import Session

base_promt = """De la sesión {begining_promt_message}. De la sesión dame el analisys {analisys}.
                ------- TOP SPEED -------
                Dame el piloto con la velocidad punta más alta y más baja. 
                Únicamente uno de cada.

                Posteriormente me devolverás esta información en este tipo de mensaje:

                🌍#hastag_gran_premio (en caso de ser test de pretemporada #PreSeasonTesting)
                🏆numero_ronda/total_rondas (En caso de test de pretemporada FP1 es First day, FP2 es Second day and FP3 es Third day)
                🏁sesion

                ------- TOP SPEED ------- Si el analisys es top speed muestra esto
                🚀piloto_velocidad_punta_mas_alta (velocidad_punta_mas_alta Km)
                🐢piloto_velocidad_punto_mas_lenta (velocidad_más_lenta Km)"""

def get_total_rounds(session: Session) -> int:
    year = session.event.EventDate.year
    schedule = fastf1.get_event_schedule(year)
    official = schedule.loc[schedule['EventFormat'] != 'testing', 'RoundNumber']
    total_rounds = official.max()
    return total_rounds

def get_beginning_prompt_message(session: Session, is_testing_session: bool = False) -> str:
    msg = f"{session.name}, "
    if is_testing_session:
        msg += f"de {session.event}"
    else:
        name_event    = session.event.EventName
        total_rounds  = get_total_rounds(session)
        msg += (
            f"la ronda número {session.event.RoundNumber} de "
            f"{total_rounds}, el cual es {name_event}"
        )
    return msg

def get_promt(session: Session, analisys: str) -> str:

    is_testing_session = session.event.is_testing()
    variables = {
        "begining_promt_message": get_beginning_prompt_message(session, is_testing_session),
        "analisys": analisys
    }
    final_promt = base_promt.format(**variables)
    return final_promt
