from utils.utils import get_laps
from collections import defaultdict

def get_top3_fastest_laps(type_event:str, year:int, event:int, session:str) -> dict:
    laps = get_laps(type_event, year, event, session)
    fastest_laps = laps.sort_values(by="LapTime").iloc[:3]

    pilotos_info = defaultdict(list)
    for _, row in fastest_laps.iterrows():
        pilotos_info[row["Driver"]].append(int(row["LapNumber"]))

    return dict(pilotos_info)