# Historical Data Archive

> This repository stores **long-term historical data** synchronized from real-time data repositories.

---

## 🔗 Source repositories

- Air-quality / PV sources: [StorywithLove/workflow](https://github.com/StorywithLove/workflow)  
- Satellite radiation source: [StorywithLove/envdata-sat](https://github.com/StorywithLove/envdata-sat)  
- Purpose: retain historical monthly batches outside the real-time acquisition repositories

---

## 🗂️ Archive Structure

- Data is organized by **source** and **date**. Sources include CNEMC, ZJEMC, PVPower, and Himawari.

- Each source is organized by date. Himawari daily CSVs are stored as:
```
Archive/
  Himawari/
    YYYY-MM-DD/
      radiation_YYYYMMDD.csv
      radiation_YYYYMMDD.status.json
```
- CNEMC and ZJEMC retain their existing hourly-file layout; PVPower retains its existing monthly layout.
---

## ⚙️ Sync Rule

- **Automatic synchronization**:  
- Runs at **11:00 AM Asia/Shanghai on the 1st day of each month** (after the previous UTC day's CSV generation)
- Synchronizes all available data of the previous month from the source repositories, including envdata-sat daily Himawari CSVs
- **Historical data handling**:  
- If certain hourly files are missing, the task **skips missing files** but continues syncing other files
- Only existing date folders are synced

---

## 📌 Notes

- CNEMC and ZJEMC follow the **same folder structure**  
- The repository is **read-only for historical data**; all updates come from automated monthly sync  
- You can manually trigger a sync for a specific month via **GitHub Actions** workflow

---

## 🏷️ Quick Overview

| Feature                  | Description                                   |
|---------------------------|-----------------------------------------------|
| Source repos              | [workflow](https://github.com/StorywithLove/workflow), [envdata-sat](https://github.com/StorywithLove/envdata-sat) |
| Sync frequency            | Monthly (1st day of month, 09:00 AM)         |
| Default sync data         | Previous month's historical data              |
| Folder structure          | `Archive/Himawari/<YYYY-MM-DD>/radiation_YYYYMMDD.csv` (other sources retain their existing layouts) |
| Missing files handling    | Skipped, with warnings                        |

---

*Maintained by the automation workflow for historical data archival.*
