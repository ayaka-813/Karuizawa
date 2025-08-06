from fastapi import FastAPI, Query
from datetime import datetime
import pandas as pd

app = FastAPI()

# CSV読み込み（UTF-8 with BOM に対応）
timetable_df = pd.read_csv("bus_timetable_route_normalized.csv", encoding="utf-8-sig")

@app.get("/bus_info")
def get_bus_info(
    destination: str = Query(..., description="目的地に最も近いバス停名（例：雲場池）"),
    current_time: str = Query(..., description="現在の時刻（ISO 8601形式）例: 2025-08-04T13:40:00Z")
):
    try:
        now = datetime.fromisoformat(current_time.replace("Z", "+00:00"))
    except ValueError:
        return {"message": "現在時刻の形式が正しくありません（ISO 8601形式）"}

    start_stop = "中軽井沢駅"
    candidate_buses = []

    # 全bus_id（便）ごとにチェック
    for bus_id in timetable_df["bus_id"].unique():
        bus_df = timetable_df[timetable_df["bus_id"] == bus_id]

        # 必要な停留所を含んでいるか確認
        stops = bus_df["stop_name"].tolist()
        if start_stop in stops and destination in stops:
            start_idx = stops.index(start_stop)
            dest_idx = stops.index(destination)

            if start_idx < dest_idx:
                # 出発時刻（中軽井沢駅）を取得
                start_row = bus_df[bus_df["stop_name"] == start_stop]
                departure_time_str = start_row.iloc[0]["time"]
                try:
                    h, m, s = map(int, departure_time_str.split(":"))
                    departure_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                    if departure_time > now:
                        minutes_left = int((departure_time - now).total_seconds() / 60)
                        route = bus_df.iloc[0]["route"]
                        candidate_buses.append({
                            "route": route,
                            "bus_id": bus_id,
                            "departure_time": departure_time.strftime("%H:%M"),
                            "minutes_left": minutes_left,
                            "message": f"{route}のバスで、中軽井沢駅を{departure_time.strftime('%H:%M')}に出発（あと{minutes_left}分後）するバスに乗ってください"
                        })
                except:
                    continue

    if not candidate_buses:
        return {"message": f"中軽井沢駅から{destination}方面へ向かうバスは見つかりませんでした。"}

    # 最も早く出るバスを選択
    best_option = sorted(candidate_buses, key=lambda x: x["minutes_left"])[0]
    return best_option
