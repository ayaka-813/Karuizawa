from fastapi import FastAPI, Query
from datetime import datetime

app = FastAPI()

@app.get("/bus_info")
def get_bus_info(
    destination: str = Query(...),
    bus_stop: str = Query(...),
    current_time: str = Query(...)
):
    # 現在時刻のパース
    try:
        now = datetime.fromisoformat(current_time.replace("Z", "+00:00"))
    except ValueError:
        return {"message": "時刻の形式が正しくありません。"}

    # 仮の時刻表（例：実際にはCSVなどで拡張可能）
    dummy_timetable = {
        "旧軽ロータリー前": ["14:10", "15:00", "16:30"],
        "星野エリア前": ["14:05", "15:20", "16:50"]
    }

    times = dummy_timetable.get(bus_stop, [])
    next_bus = None
    minutes_left = None

    for t in times:
        hour, minute = map(int, t.split(":"))
        bus_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if bus_time > now:
            next_bus = t
            minutes_left = int((bus_time - now).total_seconds() / 60)
            break

    if not next_bus:
        return {"message": f"{bus_stop} から出るバスは本日は終了しました。"}

    return {
        "destination": destination,
        "bus_stop": bus_stop,
        "next_departure": next_bus,
        "minutes_left": minutes_left,
        "message": f"{bus_stop}から{next_bus}発のバスに乗ってください（あと{minutes_left}分後）"
    }
