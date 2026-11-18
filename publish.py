import gspread
import pandas as pd
from gspread_dataframe import set_with_dataframe
from sqlalchemy import create_engine

# ตั้งค่าการเชื่อมต่อ PostgreSQL
DB_URL = "postgresql+psycopg2://admin:password123@localhost:5432/steam_dw"
engine = create_engine(DB_URL)

# ชื่อไฟล์ Google Sheets และไฟล์ Credentials
SPREADSHEET_NAME = "Steam_Games_Production"
CREDENTIALS_FILE = "credentials.json"

def run_publish():
    print("1. กำลังดึงข้อมูลที่ทำความสะอาดแล้วจาก Schema: production...")
    df = pd.read_sql("SELECT * FROM production.steam_games_cleaned", engine)
    print(f"   อ่านข้อมูลสำเร็จ: {len(df):,} แถว, {len(df.columns)} คอลัมน์")

    # แปลงค่าว่าง (NaN/None) เป็นข้อความว่าง "" เพื่อป้องกัน Error ตอนส่งขึ้น Google Sheets
    df = df.fillna("")

    print("2. กำลังเชื่อมต่อ Google Sheets API...")
    gc = gspread.service_account(filename=CREDENTIALS_FILE)
    sh = gc.open(SPREADSHEET_NAME)
    worksheet = sh.sheet1  # เลือกแผ่นงาน (Worksheet) แรก

    print(f"3. กำลังอัปโหลดข้อมูลลงไฟล์ '{SPREADSHEET_NAME}' (อาจใช้เวลา 15-30 วินาที)...")
    worksheet.clear()  # ล้างข้อมูลเก่าก่อนอัปเดตใหม่
    set_with_dataframe(worksheet, df, include_index=False, resize=True)

    print("ส่งข้อมูลขึ้น Google Sheets เสร็จสมบูรณ์!")

if __name__ == "__main__":
    run_publish()
