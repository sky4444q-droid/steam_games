import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.types import Integer

# เชื่อมต่อ PostgreSQL
DB_URL = "postgresql+psycopg2://admin:password123@localhost:5432/steam_dw"
engine = create_engine(DB_URL)

def run_transform():
    print("1. กำลังดึงข้อมูลดิบจาก Schema: raw_data...")
    df = pd.read_sql("SELECT * FROM raw_data.steam_games_wikidata", engine)
    print(f"   โหลดข้อมูลสำเร็จ: {len(df):,} แถว")

    # 2. ตัดคอลัมน์ที่ใช้งานไม่ได้ออก (metacritic_id ว่าง 100%, hltb_id มีค่าเดียว)
    df = df.drop(columns=["metacritic_id", "hltb_id"])

    # 3. แทนที่ URL blank node ใน esrb_rating และ game_engine ด้วยค่าว่าง (NaN)
    blank_node_pattern = r"^http://www\.wikidata\.org/\.well-known/genid/.*"
    df["esrb_rating"] = df["esrb_rating"].replace(blank_node_pattern, np.nan, regex=True)
    df["game_engine"] = df["game_engine"].replace(blank_node_pattern, np.nan, regex=True)

    # 4. แปลงรหัส Wikidata Q-ID ที่พบบ่อยใน game_engine เป็นชื่อเอนจินจริง
    qid_engine_map = {
        "Q63966": "Unity",
        "Q94277753": "Unreal Engine 5",
        "Q608276": "Unreal Engine",
        "Q851402": "Torque Game Engine",
        "Q14947635": "Telltale Tool",
        "Q870033": "CryEngine",
        "Q124514": "Frostbite",
        "Q30892050": "Phaser",
        "Q25932564": "LÖVE",
        "Q213136": "RPG Maker",
        "Q130900233": "Clickteam Fusion 2.5",
        "Q4036655": "Construct",
        "Q1064703": "Source",
    }
    df["game_engine_clean"] = df["game_engine"].replace(qid_engine_map)
    df["game_engine_clean"] = df["game_engine_clean"].apply(
        lambda x: "Other (Unmapped Q-ID)"
        if pd.notna(x) and str(x).startswith("Q") and str(x)[1:].isdigit()
        else x
    )

    # จัดกลุ่มตระกูลเอนจินหลัก (เช่น รวม Unreal Engine 3/4/5 เป็น Unreal Engine) สำหรับทำกราฟ Q1 และ Q3
    def get_engine_family(val):
        if pd.isna(val):
            return np.nan
        s = str(val)
        for family in ["Unity", "Unreal Engine", "RPG Maker", "CryEngine", "Source", "Frostbite", "Clickteam"]:
            if s.startswith(family):
                return family
        return s

    df["engine_family"] = df["game_engine_clean"].apply(get_engine_family)

    # 5. จัดกลุ่มเรตติ้ง ESRB (รวม Kids to Adults เข้ากับ Everyone)
    df["esrb_rating_clean"] = df["esrb_rating"].replace({"Kids to Adults": "Everyone"})

    # 6. แปลงชนิดข้อมูล opencritic_id จาก Float เป็นจำนวนเต็ม (Integer)
    df["opencritic_id"] = df["opencritic_id"].astype("Int64")
    df["opencritic_id"] = df["opencritic_id"].astype(object).where(df["opencritic_id"].notna(), None)

    # 7. สร้างคอลัมน์ใหม่ (Feature Engineering) สำหรับตอบคำถาม Q4 และ Q5
    df["has_esrb"] = df["esrb_rating_clean"].notna()
    df["has_engine"] = df["game_engine_clean"].notna()
    df["has_opencritic"] = df["opencritic_id"].notna()
    df["has_igdb"] = df["igdb_id"].notna()

    df["is_qid_name"] = df["wikidata_name"].astype(str).str.match(r"^Q\d+$", na=False)
    df["is_duplicate_name"] = df["wikidata_name"].notna() & df.duplicated(subset=["wikidata_name"], keep=False)

    # 8. สร้าง Schema ชื่อ production และบันทึกตารางปลายทาง
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS production;"))

    print("2. กำลังบันทึกข้อมูลที่ทำความสะอาดแล้วลง PostgreSQL (Schema: production)...")
    df.to_sql(
        name="steam_games_cleaned",
        con=engine,
        schema="production",
        if_exists="replace",
        index=False,
        chunksize=10000,
        dtype={"opencritic_id": Integer()},
    )
    print(f"แปลงข้อมูลและบันทึกลง production.steam_games_cleaned เสร็จสมบูรณ์! ({len(df):,} แถว, {len(df.columns)} คอลัมน์)")

if __name__ == "__main__":
    run_transform()
