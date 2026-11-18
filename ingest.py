import pandas as pd
from sqlalchemy import create_engine, text

# 1. ตั้งค่าการเชื่อมต่อ PostgreSQL (ตรงกับใน docker-compose.yml)
DB_URL = "postgresql+psycopg2://admin:password123@localhost:5432/steam_dw"
engine = create_engine(DB_URL)

def run_ingest():
    print("กำลังอ่านไฟล์ steam_games_wikidata.csv...")
    df = pd.read_csv("steam_games_wikidata.csv")
    print(f"อ่านข้อมูลสำเร็จ: {len(df):,} แถว, {len(df.columns)} คอลัมน์")

    # 2. สร้าง Schema ชื่อ raw_data ตามโจทย์
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw_data;"))

    # 3. โหลดข้อมูลดิบเข้าตาราง raw_data.steam_games_wikidata
    print("กำลังนำเข้าข้อมูลสู่ PostgreSQL (Schema: raw_data)...")
    df.to_sql(
        name="steam_games_wikidata",
        con=engine,
        schema="raw_data",
        if_exists="replace",
        index=False,
        chunksize=10000
    )
    print("นำเข้าข้อมูลดิบเสร็จสมบูรณ์!")

if __name__ == "__main__":
    run_ingest()
