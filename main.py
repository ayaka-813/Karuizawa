from fastapi import FastAPI, Query
from datetime import datetime
import pandas as pd

app = FastAPI()

# CSV読み込み（UTF-8エンコードで統一）
timetable_df = pd.read_csv("bus_timetable.csv", encoding="utf-8-sig")

def get_times_for_stop(bus_stop_name):
    # 複数行（外回り・内回り）をまとめて取得
    rows = timetable_df[timetable_df["stop_name"] == bus_stop_name]
    if rows.empty:
        return None

    # 時刻列を抽出（flattenして、重複を排除）
    time_columns = ["time_1", "time_2", "time_3", "time_4", "time_5"]
    times = pd.unique(rows[time_columns].values.ravel()).tolist()

    # 空欄やnull除去
    times = [t for t in times if pd.notnull(t)]
    return sorted(times)

@app.get("/bus_info")
def get_bus_info(
    destination: str = Query(...),
    bus_stop: str = Query(...),
    current_time: str = Query(...)
):
    try:
        now = datetime.fromisoformat(current_time.replace("Z", "+00:00"))
    except ValueError:
        return {"message": "現在時刻の形式が正しくありません（ISO形式）"}

    times = get_times_for_stop(bus_stop)
    if not times:
        return {"message": f"{bus_stop} の時刻表が見つかりませんでした。"}

    next_bus = None
    minutes_left = None

    for t in times:
        try:
            hour, minute = map(int, t.split(":"))
            bus_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if bus_time > now:
                next_bus = t
                minutes_left = int((bus_time - now).total_seconds() / 60)
                break
        except Exception:
            continue

    if not next_bus:
        return {"message": f"{bus_stop} から出るバスは本日は終了しました。"}

    return {
        "destination": destination,
        "bus_stop": bus_stop,
        "next_departure": next_bus,
        "minutes_left": minutes_left,
        "message": f"{bus_stop}から{next_bus}発のバスに乗ってください（あと{minutes_left}分後）"
    }
