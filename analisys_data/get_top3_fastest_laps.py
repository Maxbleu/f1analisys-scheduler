from utils.utils import get_laps_from_session
from collections import defaultdict

def get_top3_fastest_laps(obj_session) -> dict:
    laps = get_laps_from_session(obj_session)
    fastest_laps = laps.sort_values(by="LapTime").iloc[:3]

    pilotos_info = defaultdict(list)
    for _, row in fastest_laps.iterrows():
        pilotos_info[row["Driver"]].append(int(row["LapNumber"]))

    return dict(pilotos_info)