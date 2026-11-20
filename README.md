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
- CNEMC and ZJEMC retain their existing hourly-file layout; PVPower retains its existing monthly layout. Himawari monthly manifests are stored at `Archive/Himawari/_manifests/YYYY-MM.json`.
---

## ⚙️ Sync Rule

- **Automatic synchronization**:  
- Runs at **11:00 AM Asia/Shanghai on the 1st day of each month** (after the previous UTC day's CSV generation)
- Synchronizes the previous month's data from the source repositories, including envdata-sat daily Himawari CSVs. Himawari archiving is all-or-nothing for the month: every calendar day must be present with its CSV and quality sidecar.
- **Historical data handling**:  
- If certain hourly files are missing, the task **skips missing files** but continues syncing other files
- Only existing date folders are synced
- Before archiving Himawari, each day is validated for all 31 configured stations and exactly 144 UTC interval-end timestamps per station (00:10 through next-day 00:00), native 600-second labels, model identity, quality flags, and consistency with its status JSON
- After copying, SHA-256 hashes are compared with the source files; a monthly JSON manifest records per-day hashes, row counts, valid/missing counts, and quality-flag totals
- Monthly archive runs are serialized so scheduled and manually triggered syncs cannot write concurrently

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
| Sync frequency            | Monthly (1st day of month, 11:00 AM Asia/Shanghai) |
| Default sync data         | Previous month's historical data              |
| Folder structure          | `Archive/Himawari/<YYYY-MM-DD>/radiation_YYYYMMDD.csv` (other sources retain their existing layouts) |
| Missing files handling    | Skipped for existing CNEMC/ZJEMC/PVPower flows; incomplete Himawari months fail before commit |
| Himawari validation       | 31 stations × 144 intervals/day; sidecar checks; SHA-256 manifest |

---

*Maintained by the automation workflow for historical data archival.*
