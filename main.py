from fastapi import FastAPI, Query
from datetime import datetime
import pandas as pd

app = FastAPI()

# CSV読み込み（エンコーディング注意）
timetable_df = pd.read_csv("bus_timetable.csv", encoding="utf-8-sig")

def get_times_for_stop(bus_stop_name):
    row = timetable_df[timetable_df["stop_name"] == bus_stop_name]
    if row.empty:
        return None
    # "time_1"〜"time_5" だけを抽出
    time_columns = ["time_1", "time_2", "time_3", "time_4", "time_5"]
    return row[time_columns].values.flatten().tolist()

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
