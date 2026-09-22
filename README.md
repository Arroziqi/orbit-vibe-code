# Orbit — Task Scheduling & Quota System

Proyek ini berisi dua pendekatan solusi untuk tugas scheduling dan quota user:

- `solution_claude_model/` — solusi yang dibuat dengan pendekatan modular yang lebih sederhana, mirip arsitektur refactor awal.
- `src/` — solusi yang lebih terstruktur dan siap untuk produksi, dengan pemisahan domain, use case, infrastructure, dan composition.

Tujuan utama dari kedua solusi adalah sama: menjalankan tugas sesuai jam yang ditentukan, menjaga kuota harian per user, dan mengizinkan strategi eksekusi yang extensible.

---

## 1. Ringkasan proyek

Sistem ini menangani skenario seperti:

- setiap user punya quota harian
- tugas dijadwalkan berdasarkan waktu (`HH:MM`)
- tugas bisa berupa `sync`, `backup`, atau `delete`
- saat waktu task tiba, sistem mengecek kuota user sebelum menjalankan aksi
- jika kuota habis, task dilewati tanpa menghentikan scheduler
- log dibuat untuk tracing eksekusi dan error

---

## 2. Struktur folder

```text
orbit/
├── README.md
├── pyproject.toml
├── guidence.md
├── test.md
├── src/
│   ├── composition/
│   ├── domain/
│   ├── infrastructure/
│   └── usecase/
├── solution_claude_model/
│   ├── async_scheduler.py
│   ├── executors.py
│   ├── main.py
│   ├── models.py
│   ├── README.md
│   ├── scheduler.py
│   ├── test_scheduler.py
│   └── user_manager.py
└── tests/
    └── test_all.py
```

---

## 3. Solusi yang tersedia

### A. Solusi dari Claude

Lokasi: `solution_claude_model/`

Karakteristik:

- fokus pada refactor modular
- `Task` sebagai model data
- `UserManager` mengatur quota dan user registry
- `Scheduler` memeriksa task yang jatuh tempo
- `ExecutorFactory` mendaftarkan strategi per action
- format sederhana dan mudah dipahami untuk interview / demo

Entry point:

```bash
python -m solution_claude_model.main
```

Bisa juga dijalankan langsung dari folder:

```bash
cd solution_claude_model
python main.py
```

---

### B. Solusi model free / struktur yang lebih rapi

Lokasi: `src/`

Karakteristik:

- arsitektur layered: `domain`, `usecase`, `infrastructure`, `composition`
- model `User`, `Task`, `ExecutionResult` lebih formal
- quota logic dipisah ke `QuotaService`
- action strategy memakai `ActionRegistry`
- validasi konfigurasi lebih kuat
- test otomatis di `tests/test_all.py`

Entry point utama:

```bash
python -m src.composition.root
```

Untuk menjalankan demo satu kali tanpa loop scheduler:

```bash
python - <<'PY'
from src.composition.root import create_app
app = create_app()
results = app.run_once()
print([(r.task.action, r.outcome.value, r.message) for r in results])
PY
```

---

## 4. Perbandingan dua solusi

| Aspek                  | `solution_claude_model`            | `src/`                                  |
| ---------------------- | ---------------------------------- | --------------------------------------- |
| Fokus                  | Refactor cepat dan mudah dibaca    | Arsitektur modular yang lebih formal    |
| Domain model           | Sederhana                          | Lebih jelas dan structured              |
| Quota logic            | `UserManager`                      | `QuotaService` + `User` model           |
| Strategy dispatch      | `ExecutorFactory`                  | `ActionRegistry`                        |
| Validation             | Minimal                            | Lebih kuat dan terstruktur              |
| Testing                | Ada test tertentu di folder solusi | `tests/test_all.py` lebih lengkap       |
| Kesesuaian untuk scale | Cukup untuk demo / interview       | Lebih cocok untuk sistem yang diperluas |

---

## 5. Menjalankan test

Untuk solusi berbasis root:

```bash
python -m pytest
```

Jika ingin menjalankan test spesifik:

```bash
python -m pytest tests/test_all.py
```

---

## 6. Catatan penggunaan

- Jika `python` tidak terdeteksi di mesin Anda, gunakan `python3` atau full path ke interpreter Python Anda.
- Untuk environment Windows, sering juga bisa dipanggil dengan:

```bash
py -m pytest
```

- `solution_claude_model` lebih cocok untuk memahami alur logika secara cepat.
- `src/` lebih cocok jika ingin mengevaluasi desain yang lebih clean, reviewable, dan dapat dikembangkan lebih lanjut.

---

## 7. Kesimpulan

Project ini merepresentasikan dua tahap evolusi solusi:

1. solusi awal yang modular dan mudah dipahami (`solution_claude_model`)
2. solusi yang lebih rapi dan sistematis (`src/`) dengan pemisahan concern yang lebih jelas

Pilihan terbaik tergantung kebutuhan:

- untuk demo / interview: gunakan `solution_claude_model`
- untuk desain yang lebih siap dikembangkan: gunakan `src/`

---

## 8. Referensi tambahan

- README solusi Claude: `solution_claude_model/README.md`
- Panduan tugas: `guidence.md`
- Konstitusi/aturan tugas: `CONSTITUTION.md`
