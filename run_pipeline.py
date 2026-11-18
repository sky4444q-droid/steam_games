import time
from ingest import run_ingest
from publish import run_publish
from transform import run_transform

def main():
    start_time = time.time()
    print("=== เริ่มต้นการทำงาน Automated Data Pipeline ===")

    print("\n[Phase 2] ขั้นตอนการดึงและโหลดข้อมูลดิบ (Ingestion & Load)")
    run_ingest()

    print("\n[Phase 3] ขั้นตอนการทำความสะอาดและแปลงข้อมูล (Transformation)")
    run_transform()

    print("\n[Phase 4] ขั้นตอนการส่งข้อมูลขึ้น Google Sheets (Publication)")
    run_publish()

    elapsed = time.time() - start_time
    print(f"\n=== รัน Pipeline ทั้งหมดเสร็จสมบูรณ์ใน {elapsed:.2f} วินาที ===")

if __name__ == "__main__":
    main()
