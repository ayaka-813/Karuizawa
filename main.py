from fastapi import FastAPI, Query
from datetime import datetime
import pandas as pd

app = FastAPI()

# 読み込むCSVファイル（整形済み）
timetable_df = pd.read_csv("bus_timetable_route_normalized.csv", encoding="utf-8-sig")

@app.get("/bus_info")
def get_bus_info(
    destination: str = Query(..., description="目的地に最も近いバス停名（例：雲場池）"),
    current_time: str = Query(..., description="現在の時刻（ISO8601形式、例：2025-08-04T13:40:00Z）")
):
    try:
        now = datetime.fromisoformat(current_time.replace("Z", "+00:00"))
    except ValueError:
        return {"message": "現在時刻の形式が正しくありません（ISO8601形式で入力してください）"}

    origin = "中軽井沢駅"

    # 中軽井沢駅に停車するbus_id
    origin_buses = timetable_df[timetable_df["stop_name"] == origin]["bus_id"].unique()
    candidate_buses = []

    for bus_id in origin_buses:
        df_bus = timetable_df[timetable_df["bus_id"] == bus_id]
        stops = df_bus["stop_name"].tolist()

        if destination in stops:
            origin_order = df_bus[df_bus["stop_name"] == origin]["stop_order"].values[0]
            dest_order = df_bus[df_bus["stop_name"] == destination]["stop_order"].values[0]

            if origin_order < dest_order:
                departure_time_str = df_bus[df_bus["stop_name"] == origin]["time"].values[0]
                try:
                    hour, minute = map(int, str(departure_time_str).split(":"))
                    departure_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if departure_time > now:
                        minutes_left = int((departure_time - now).total_seconds() / 60)
                        candidate_buses.append({
                            "route": df_bus["route"].values[0],
                            "bus_id": bus_id,
                            "departure_time": departure_time_str,
                            "minutes_left": minutes_left
                        })
                except:
                    continue

    if not candidate_buses:
        return {"message": f"{origin}から{destination}へ行けるバスは見つかりませんでした。"}

    # 最も早く出発するバスを選択
    next_bus = sorted(candidate_buses, key=lambda x: x["minutes_left"])[0]
    return {
        "route": next_bus["route"],
        "bus_id": next_bus["bus_id"],
        "departure_time": next_bus["departure_time"],
        "minutes_left": next_bus["minutes_left"],
        "message": f"{next_bus['route']}のバスで、中軽井沢駅を{next_bus['departure_time']}に出発（あと{next_bus['minutes_left']}分後）するバスに乗ってください"
    }
