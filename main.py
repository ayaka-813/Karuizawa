from fastapi import FastAPI, Query
from datetime import datetime
import pandas as pd

app = FastAPI()

# CSVファイルを読み込む（ファイル名はご自身のものに合わせてください）
timetable_df = pd.read_csv("bus_timetable.csv", encoding="shift_jis")

def get_times_for_stop(bus_stop_name):
    row = timetable_df[timetable_df["stop_name"] == bus_stop_name]
    if row.empty:
        return None
    times = row.iloc[0, 2:].dropna().tolist()
    return times

@app.get("/bus_info")
def get_bus_info(
    destination: str = Query(...),
    bus_stop: str = Query(...),
    current_time: str = Query(...)
):
    # 現在時刻の形式チェック
    try:
        now = datetime.fromisoformat(current_time.replace("Z", "+00:00"))
    except ValueError:
        return {"message": "現在時刻の形式が正しくありません（ISO 8601形式で渡してください）"}

    times = get_times_for_stop(bus_stop)
    if not times:
        return {"message": f"{bus_stop} の時刻表データが見つかりませんでした。"}

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
        return {"message": f"{bus_stop} から出る本日のバスは終了しました。"}

    return {
        "destination": destination,
        "bus_stop": bus_stop,
        "next_departure": next_bus,
        "minutes_left": minutes_left,
        "message": f"{bus_stop}から{next_bus}発のバスに乗ってください（あと{minutes_left}分後）"
    }
