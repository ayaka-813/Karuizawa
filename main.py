from fastapi import FastAPI, Query
from datetime import datetime, timedelta
import pandas as pd

app = FastAPI()

# 時刻表の読み込み（タブ区切り + Shift_JIS）
timetable_df = pd.read_csv("bus_timetable_final.csv", encoding="shift_jis", sep="\t")

# 中軽井沢駅から目的地に停車する便を抽出する関数
def find_next_bus(destination_stop: str, current_time_str: str):
    try:
        now = datetime.fromisoformat(current_time_str.replace("Z", "+00:00"))
    except ValueError:
        return {"message": "現在時刻の形式が正しくありません（ISO8601形式：例 2025-08-04T13:40:00Z）"}

    # 目的地と中軽井沢駅の両方を含むルートのみ対象に
    candidate_routes = []
    for route in timetable_df["route"].unique():
        route_df = timetable_df[timetable_df["route"] == route]
        stops = route_df["stop_name"].tolist()
        if "中軽井沢駅" in stops and destination_stop in stops:
            start_idx = stops.index("中軽井沢駅")
            dest_idx = stops.index(destination_stop)
            if start_idx < dest_idx:
                candidate_routes.append(route)

    # 候補ルートの中から、出発時刻を調べる
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
                        bus_time = now.repl_
