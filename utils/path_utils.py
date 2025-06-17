import requests
from analisys_data import get_top3_fastest_laps

def get_pilotos_info_path():
    try:
        api_analisys_url = "https://f1analisys-production.up.railway.app"
        response = requests.get(api_analisys_url+"/openapi.json")
        if response.status_code == 200:
            data = response.json()
            return [path for path in data["paths"].keys() if "pilotos_info" in path.lower()]
    except Exception as e:
        print(f"[X] Error {e}")
    return []

def get_drivers_laps_path(drivers_laps_range: dict) -> str:
    drivers_path = "/compare"
    keys_list = list(drivers_laps_range.keys())
    for driver in keys_list:
        lap_range = drivers_laps_range[driver]
        drivers_path += f"/{driver}"
        for lap in lap_range:
            drivers_path += f"/{lap}"
        if keys_list.index(driver) < len(keys_list) - 1:
            drivers_path += "/vs"
    return drivers_path

def get_full_path(type_event, year, event, session, analisys):
    full_path = f"/{type_event}/{analisys}/{year}/{event}/{session}"
    pilotos_paths = get_pilotos_info_path()
    result = any(analisys in path for path in pilotos_paths)
    if result:
        drivers_laps = get_top3_fastest_laps(type_event, year, event, session)
        drivers_path = get_drivers_laps_path(drivers_laps)
        full_path = full_path+drivers_path
    return full_path