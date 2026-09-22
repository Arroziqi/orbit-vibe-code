# Task Scheduling & Quota System — Refactor

## Struktur modul

| File | Tanggung jawab |
|---|---|
| `models.py` | `Task` — data model murni, tervalidasi (format waktu), bisa dibangun dari dict (`Task.from_dict`). |
| `user_manager.py` | `User` + `UserManager` — registrasi user, cek & konsumsi kuota, reset harian. Tidak tahu apa-apa soal task/eksekusi. |
| `executors.py` | Strategy pattern: `BaseExecutor` (abstract) + `SyncExecutor`/`BackupExecutor`/`DeleteExecutor`, didaftarkan lewat decorator `@register("nama_action")` ke `ExecutorFactory`. Menambah action baru = tambah 1 class, tanpa mengubah scheduler. |
| `scheduler.py` | `Scheduler` — mengecek task yang jatuh tempo pada waktu tertentu, cek kuota lewat `UserManager`, lalu dispatch ke `ExecutorFactory`. Semua error (kuota habis, user tak dikenal, action tak dikenal, exception tak terduga) ditangani per-task agar satu task rusak tidak menghentikan seluruh loop. |
| `async_scheduler.py` | Versi opsional: task-task yang due dijalankan konkuren via `asyncio.gather`, masing-masing tetap mengecek kuota secara sinkron sebelum kerja async-nya jalan. |
| `main.py` | Entry point — mengganti `run()` lama; user & task sekarang datang dari dict config (`USERS_CONFIG` / `TASKS_CONFIG`), bukan hardcoded di badan fungsi. |
| `test_scheduler.py` | 11 unit test: validasi model, enforcement kuota, factory lookup, scheduler dispatch, dan skip-tapi-tidak-crash untuk user/aksi tak dikenal. |

Semua module sudah dijalankan (`python3 main.py`, test suite, dan demo async) dan hasilnya cocok dengan perilaku skrip lama.

## Jawaban untuk pertanyaan interview

**Bagaimana desain prompt untuk mengarahkan AI?**
Saya tidak minta "refactor kode ini" secara umum. Saya kasih target arsitektur secara eksplisit: pisahkan jadi User/Quota, Task model, Executor (strategy pattern + registry supaya extensible), dan Scheduler yang hanya orkestrasi — lalu minta logging di titik-titik kegagalan (kuota habis, user tak dikenal, action tak dikenal), bukan cuma `print`. Prompt yang eksplisit soal *boundary tanggung jawab tiap kelas* jauh lebih penting daripada minta "buat lebih rapi".

**Ada saran AI yang saya tolak?**
Ya — draf awal AI menaruh exception handling generik (`except Exception: pass`) di dalam `UserManager.record_execution`, yang akan menelan bug nyata (misalnya typo nama user) secara diam-diam. Saya ganti jadi exception spesifik (`QuotaExceededError`, `UnknownUserError`) yang ditangkap secara eksplisit di layer `Scheduler`, supaya kegagalan quota vs kegagalan konfigurasi tetap bisa dibedakan di log.

**Kalau harus menangani puluhan ribu task per hari, bagaimana scale-nya?**
- Ganti polling loop (`run_once` tiap menit) dengan scheduler berbasis event/queue (misalnya Celery beat + broker, atau APScheduler dengan job store di DB) supaya tidak scan seluruh list task tiap tick.
- Pindahkan state user/kuota dari in-memory dict ke storage persisten (Redis untuk counter cepat, atau Postgres) supaya beberapa worker bisa berbagi state dan restart tidak menghilangkan kuota terpakai.
- Jadikan eksekusi task sebagai pekerjaan async/terdistribusi (worker pool) — `async_scheduler.py` adalah langkah pertama ke arah situ; skala penuh berarti worker terpisah per action type, dengan retry & dead-letter queue.
- Tambahkan idempotency key per task-run supaya restart/duplikasi tidak mengeksekusi task dua kali.

**Bagian mana yang bisa diekstrak jadi modul reusable untuk tim lain?**
`user_manager.py` (kuota generik, tidak terikat konsep "task") dan mekanisme registry di `executors.py` (strategy + factory pattern) keduanya generik dan bisa dipakai ulang untuk sistem lain yang butuh "quota per user" atau "pluggable action handler", terlepas dari domain scheduling ini.
