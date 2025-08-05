from fastapi import FastAPI, Query
from datetime import datetime, timedelta
import pandas as pd

app = FastAPI()

# タブ区切り＋Shift_JIS でバス時刻表CSVを読み込む
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
