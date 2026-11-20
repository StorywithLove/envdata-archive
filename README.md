# Historical Data Archive

> This repository stores **long-term historical data** synchronized from real-time data repositories.

---

## 🔗 Real-Time Database

- Air-quality / PV sources: [StorywithLove/workflow](https://github.com/StorywithLove/workflow)  
- Satellite radiation source: [StorywithLove/envdata-sat](https://github.com/StorywithLove/envdata-sat)  
- Purpose: retain historical monthly batches outside the real-time acquisition repositories

---

## 🗂️ Archive Structure

- Data is organized by **source** and **date**. Sources include CNEMC, ZJEMC, PVPower, and Himawari.

- Each day has **one folder**, ideally containing **24 hourly CSV files**.
```
Archive/  
  CNEMC/  
    YYYY-MM-DD/
      YYYY-MM-DDT00.csv
      YYYY-MM-DDT01.csv
    ...
```
---

## ⚙️ Sync Rule

- **Automatic synchronization**:  
- Runs at **09:00 AM on the 1st day of each month**
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
| Folder structure          | `Archive/<Source>/<YYYY-MM-DD>/<CSV files>` |
| Missing files handling    | Skipped, with warnings                        |

---

*Maintained by the automation workflow for historical data archival.*
