# Steam Games Automated Data Pipeline

Pipeline สำหรับดึงข้อมูลเกม Steam จาก Wikidata (`steam_games_wikidata.csv`) → โหลดเข้า PostgreSQL → ทำความสะอาดและสร้างฟีเจอร์ → ส่งขึ้น Google Sheets → แสดงผลบน Looker Studio Dashboard

**Looker Studio Dashboard:** <ใส่ลิงก์ Dashboard ที่นี่>

---

## สถาปัตยกรรม (Architecture)

```
steam_games_wikidata.csv
        │  ingest.py
        ▼
PostgreSQL (Docker)  ── schema: raw_data.steam_games_wikidata
        │  transform.py
        ▼
PostgreSQL           ── schema: production.steam_games_cleaned
        │  publish.py  (Google Sheets API / Service Account)
        ▼
Google Sheets: "Steam_Games_Production"
        │
        ▼
Looker Studio Dashboard
```

`run_pipeline.py` เรียกทั้ง 3 ขั้นตอนต่อกันอัตโนมัติด้วยคำสั่งเดียว (ทั้งหมดใช้เวลาประมาณ 50 วินาที)

| ไฟล์ | หน้าที่ |
|---|---|
| `docker-compose.yml` | รัน PostgreSQL 15 (container `steam_postgres`, database `steam_dw`, port 5432) |
| `ingest.py` | อ่าน CSV (128,348 แถว, 8 คอลัมน์) แล้วโหลดเข้า `raw_data.steam_games_wikidata` |
| `transform.py` | ทำความสะอาดข้อมูล สร้างฟีเจอร์ใหม่ แล้วบันทึกลง `production.steam_games_cleaned` (15 คอลัมน์) |
| `publish.py` | ดึงข้อมูลจาก `production` แล้วเขียนทับลง Google Sheets (ล้างข้อมูลเก่าก่อนทุกครั้ง) |
| `run_pipeline.py` | รันทั้ง pipeline ตั้งแต่ต้นจนจบ และจับเวลา |

## ขั้นตอนการแปลงข้อมูล (transform.py)

1. ลบคอลัมน์ที่ใช้งานไม่ได้: `metacritic_id` (ว่าง 100%) และ `hltb_id` (มีค่าเดียว)
2. แทนที่ค่า Wikidata blank node (`http://www.wikidata.org/.well-known/genid/...`) ใน `esrb_rating` และ `game_engine` ด้วยค่าว่าง
3. แปลงรหัส Q-ID ของเอนจินที่พบบ่อยเป็นชื่อจริง (เช่น `Q63966` → Unity) เก็บใน `game_engine_clean` ส่วน Q-ID ที่ไม่รู้จักจัดเป็น `Other (Unmapped Q-ID)`
4. จัดกลุ่มตระกูลเอนจิน (`engine_family`) เช่น รวม Unreal Engine ทุกเวอร์ชันเป็น `Unreal Engine`
5. จัดกลุ่มเรตติ้ง ESRB (`esrb_rating_clean`) รวม `Kids to Adults` เข้ากับ `Everyone`
6. แปลง `opencritic_id` จาก float เป็น integer
7. สร้างคอลัมน์ใหม่ (feature engineering)
   - `has_esrb`, `has_engine`, `has_opencritic`, `has_igdb`: บอกว่าเกมนั้นมีข้อมูลแต่ละประเภทหรือไม่
   - `is_qid_name`: ชื่อเกมยังเป็นรหัส Q-ID (ยังไม่มีชื่อจริง)
   - `is_duplicate_name`: ชื่อเกมซ้ำกับเกมอื่น

## วิธีรัน

**สิ่งที่ต้องมี:** Docker Desktop, Python 3.10+, ไฟล์ `credentials.json` ของ Google Service Account (ไม่ได้อยู่ใน repo นี้) และ Google Sheet ชื่อ `Steam_Games_Production` ที่แชร์สิทธิ์ Editor ให้อีเมลของ Service Account แล้ว

```bash
# 1. ติดตั้งไลบรารี
pip install -r requirements.txt

# 2. เปิดฐานข้อมูล PostgreSQL
docker-compose up -d

# 3. วางไฟล์ credentials.json ไว้ในโฟลเดอร์โปรเจกต์ แล้วรัน pipeline
python run_pipeline.py
```

ตัวอย่างผลลัพธ์:

```
=== เริ่มต้นการทำงาน Automated Data Pipeline ===
[Phase 2] ขั้นตอนการดึงและโหลดข้อมูลดิบ (Ingestion & Load)
อ่านข้อมูลสำเร็จ: 128,348 แถว, 8 คอลัมน์
[Phase 3] ขั้นตอนการทำความสะอาดและแปลงข้อมูล (Transformation)
แปลงข้อมูลและบันทึกลง production.steam_games_cleaned เสร็จสมบูรณ์! (128,348 แถว, 15 คอลัมน์)
[Phase 4] ขั้นตอนการส่งข้อมูลขึ้น Google Sheets (Publication)
ส่งข้อมูลขึ้น Google Sheets เสร็จสมบูรณ์!
=== รัน Pipeline ทั้งหมดเสร็จสมบูรณ์ใน 51.41 วินาที ===
```

## หมายเหตุด้านความปลอดภัย

- `credentials.json` และ `.env` อยู่ใน `.gitignore` จึงไม่ถูกอัปโหลดขึ้น GitHub
- รหัสผ่าน PostgreSQL ใน `docker-compose.yml` ใช้สำหรับการพัฒนาในเครื่องเท่านั้น
