from fastapi import FastAPI, Query
from datetime import datetime, timedelta
import pandas as pd

app = FastAPI()

# タブ区切り + Shift_JIS でバス時刻表CSVを読み込む
timetable_df = pd.read_csv("bus_timetable_final.csv", encoding="shift_jis", sep="\t")

# 中軽井沢駅から目的地に行けるバスのうち、最も早いものを探す関数
def find_next_bus(destination_stop: str, current_time_str: str):
    try:
        now = datetime.fromisoformat(current_time_str.replace("Z", "+00:00"))
    except ValueError:
        return {"message": "現在時刻の形式が正しくありません（ISO8601形式：例 2025-08-04T13:40:00Z）"}

    # 中軽井沢駅と目的地の両方を通るルートを抽出（中軽井沢 → 目的地の順）
    candidate_routes = []
    for route in timetable_df["route"].unique():
        route_df = timetable_df[timetable_df["route"] == route]
        stops = route_df["stop_name"].tolist()
        if "中軽井沢駅" in stops and destination_stop in stops:
            start_idx = stops.index("中軽井沢駅")
            dest_idx = stops.index(destination_stop)
            if start_idx < dest_idx:
                candidate_routes.append(route)

    # 各候補ルートの出発時間を調べる
    best_option = None
    for route in candidate_routes:
        route_df = timetable_df[timetable_df["route"] == route]
        start_row = route_df[route_df["stop_name"] == "中軽井沢駅"].iloc[0]
        dest_row = route_df[route_df["stop_name"] == destination_stop].iloc[0]

        for col in timetable_df.columns:
            if col.startswith("time_"):
                start_time_val = start_row.get(col)
                dest_time_val = dest_row.get(col)
                if pd.notna(start_time_val) and pd.notna(dest_time_val):
                    try:
                        h, m = map(int, str(start_time_val).split(":")[:2])
                        bus_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                        if bus_time < now:
                            bus_time += timedelta(days=1)  # 翌日対応
                        wait_minutes = int((bus_time - now).total_seconds() / 60)

                        if not best_option or bus_time < best_option["bus_time"]:
                            best_option = {
                                "route": route,
                                "start_time": f"{h:02d}:{m:02d}",
                                "wait_minutes": wait_minutes,
                                "bus_time": bus_time
                            }
                    except:
                        continue

    if not best_option:
        return {"message": f"現在時刻以降に中軽井沢駅から{destination_stop}に行けるバスは見つかりませんでした。"}

    return {
        "route": best_option["route"],
        "departure_time": best_option["start_time"],
        "minutes_left": best_option["wait_minutes"],
        "message": f"{best_option['route']}のバスで、中軽井沢駅を{best_option['start_time']}に出発（あと{best_option['wait_minutes']}分後）するバスに乗ってください"
    }

# 🔗 FastAPIエンドポイント（Swagger UIでも表示される）
@app.get("/bus_info")
def get_bus_info(
    destination: str = Query(..., description="目的地に最も近いバス停名"),
    current_time: str = Query(..., description="現在の時刻（ISO8601形式）")
):
    return find_next_bus(destination, current_time)
