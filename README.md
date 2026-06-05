# 🛩️ DJI Mini → Xbox Controller

Aplikasi desktop (Windows) yang mengubah **remote DJI Mavic Mini** (DJI MR1SD25) menjadi **Virtual Xbox 360 Controller**. Remote dibaca lewat serial USB, lalu dipetakan ke gamepad virtual via [`vgamepad`](https://github.com/yannbouteiller/vgamepad) + [ViGEmBus](https://github.com/nefarius/ViGEmBus) — jadi stik DJI lo kebaca seperti controller biasa di game/simulator apa pun.

Dibangun di atas script CLI asli (`main.py`) dengan tambahan UI: auto-detect port, visualisasi analog live, kalibrasi penuh, dan panel log dengan deteksi lag.

---

## ▶️ Cara Run (Quick Start — Windows)

> ⚠️ Install **ViGEmBus** dulu (sekali aja): https://github.com/nefarius/ViGEmBus/releases

**1. Setup (sekali pertama):**
```bash
git clone https://github.com/firdanmanggalap/djiminicontroller.git
cd djiminicontroller
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**2. Run (tiap mau dipakai):**
```bash
cd djiminicontroller
.venv\Scripts\activate
python app.py
```

3. **Colok remote DJI** lewat USB → aplikasi otomatis nyari & nyambung (status pojok kanan atas jadi hijau **"● Connected — COMx"**). Buka game/simulator, controller udah kebaca sebagai Xbox 360.

> Kalau pakai **PowerShell** dan kena error execution policy pas `activate`, jalankan: `Set-ExecutionPolicy -Scope Process RemoteSigned` lalu ulangi. Atau pakai Command Prompt (cmd).
> Belum kepasang ViGEmBus? Aplikasi tetap kebuka tapi kasih dialog peringatan, dan output gamepad nggak aktif sampai ViGEmBus diinstall.

---

## ✨ Fitur

| | Fitur |
|---|---|
| 🔌 | **Auto-detect + auto-reconnect** — scan port sendiri, kenali remote DJI lewat probing, nyambung otomatis, dan nyambung balik kalau kabel kecabut. Nggak perlu ketik COM port manual. |
| 🕹️ | **Visualisasi analog live** — 2 stik (kiri Throttle/Yaw, kanan Pitch/Roll) + bar dial kamera. Dot mengikuti **posisi fisik** stik, buat cek pembacaan udah bener. |
| 🔄 | **Invert per-axis** — toggle langsung di UI. Invert hanya memengaruhi output ke game; tampilan tetap menunjukkan arah fisik. |
| 🎯 | **Kalibrasi penuh** — deadzone, trim titik tengah, dan range/sensitivitas per-axis. Disimpan otomatis ke `config.json`. Ada tombol Reset. |
| 🎮 | **Output ON/OFF** — hentikan/lanjutkan kirim ke virtual gamepad tanpa nutup aplikasi. |
| 📊 | **Panel log live + deteksi lag** — indikator Hz/interval, peringatan otomatis kalau gap antar-paket melonjak (lag) + estimasi paket drop, plus tombol Pause / Clear / Simpan ke file. |

---

## 📋 Requirements

### Hardware
- **Remote DJI Mavic Mini (DJI MR1SD25)** + kabel USB ke PC.
- Remote dalam keadaan menyala.

### Software (Windows)
- **Windows 10 / 11**
- **Python 3.10+** — pastikan dicentang "Add Python to PATH" saat install.
- **ViGEmBus driver** — driver sistem yang dipakai buat bikin virtual Xbox controller.
  Download & install dari rilis resmi: **https://github.com/nefarius/ViGEmBus/releases** (ambil installer `.exe` terbaru, install, restart kalau diminta).
- **Python packages** (lihat `requirements.txt`):

  | Package | Fungsi |
  |---|---|
  | `PySide6` | UI desktop (Qt) |
  | `pyserial` | baca serial port + scan port |
  | `vgamepad` | output ke Virtual Xbox 360 (butuh ViGEmBus) |
  | `pytest` | menjalankan test (opsional, buat development) |

> **Catatan:** Aplikasi ini **Windows-only** karena `vgamepad`/ViGEmBus cuma jalan di Windows. Di Linux/macOS cuma test yang bisa dijalankan, GUI + output gamepad nggak.

---

## 🚀 Instalasi & Menjalankan (Windows)

1. Install **ViGEmBus** dulu (link di atas).
2. Clone repo dan masuk foldernya:
   ```bash
   git clone https://github.com/firdanmanggalap/djiminicontroller.git
   cd djiminicontroller
   ```
3. Bikin virtual environment + install dependency:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Colok remote DJI lewat USB, lalu jalankan:
   ```bash
   python app.py
   ```

Aplikasi akan otomatis nyari remote-nya — status di pojok kanan atas berubah dari amber **"Mencari remote…"** jadi hijau **"● Connected — COMx"** dalam beberapa detik.

---

## 🖥️ Panduan UI

- **Header** — judul, indikator `⟳ Hz · interval ms · drop`, status koneksi, dan tombol **Output: ON/OFF**.
- **Panel kiri (Live)** — dua pad analog (dot ikut gerakan stik fisik) + nilai numerik, plus bar **dial kamera → Right Trigger**.
- **Panel kanan (Kalibrasi)** — per-axis: **Invert** (centang), **Deadzone** (0–30%), **Trim** (geser titik tengah), **Range** (0.5×–1.5× sensitivitas). Semua auto-save. Ada tombol **Reset**.
- **Panel bawah (Log)** — log live (scan/connect, rate, peringatan lag, reconnect). Tombol **Pause**, **Clear**, **💾 Simpan ke file** (`session.log`).

### Tips kalibrasi
- **Dot gerak kebalik dari stik fisik di game?** → toggle **Invert** axis itu.
- **Stik ngelayang pas dilepas (drift)?** → naikin **Deadzone** axis itu.
- **Titik netral nggak pas di tengah?** → setel **Trim**.
- **Mau lebih/kurang sensitif?** → setel **Range**.

Setelan tersimpan di `config.json` (di folder aplikasi) dan ke-load otomatis pas dibuka lagi.

---

## 🧠 Cara kerja (singkat)

```
serial_link.py (QThread)   baca paket 38-byte dari remote → parse 5 axis → deteksi lag → auto-reconnect
        │ Qt signals (rawAxes / status / stats / log)
        ▼
main_window.py             mapping.py: raw → trim → deadzone → range → invert → Xbox int16
        ├──► AnalogStick    tampilkan posisi fisik (dot live)
        └──► gamepad_out.py  vgamepad.VX360Gamepad → Virtual Xbox 360 (output respect invert)
config.py ↔ config.json    simpan/muat kalibrasi · logger.py → panel log + session.log
```

Remote DJI dibaca pada **115200 baud**; aplikasi mengirim paket *ping* berulang dan menunggu balasan **38 byte** yang berisi 4 nilai stik + 1 dial kamera (little-endian). Deteksi port dilakukan dengan *probing* (kirim ping, cek balasan 38 byte) — jadi nggak tergantung VID/PID.

---

## 🧪 Development & Testing

Semua logika inti (parsing, mapping, config, deteksi lag, log) terpisah dari I/O & UI, jadi bisa di-test tanpa hardware (dan tanpa `vgamepad`/Windows):

```bash
python -m pytest -q
```

41 unit test mencakup `protocol`, `mapping`, `config`, `lag_detector`, `logger`, `gamepad_out`, `serial_probe`, widget, dan wiring `main_window` (pakai fake serial + injected gamepad). Path serial/gamepad/GUI yang butuh hardware diverifikasi manual di Windows.

Struktur:
```
app.py                  entry point
dji_xbox/
  protocol.py           konstanta + parse paket (pure)
  mapping.py            kalibrasi raw → Xbox int16 (pure)
  config.py             load/save config.json
  lag_detector.py       rate Hz + deteksi lag (pure)
  logger.py             buffer log + opsional file
  gamepad_out.py        wrapper vgamepad
  serial_link.py        QThread baca serial + reconnect
  widgets/analog_stick.py   widget analog custom
  main_window.py        UI utama
tests/                  unit test
main.py                 script CLI asli (referensi)
```

---

## 🛠️ Troubleshooting

| Masalah | Solusi |
|---|---|
| `Gagal membuat sirkuit Xbox` / dialog "ViGEmBus belum siap" | ViGEmBus belum terinstall — install dari [releases](https://github.com/nefarius/ViGEmBus/releases), restart, jalankan lagi. |
| Status mentok di "Mencari remote…" | Pastikan remote nyala & kabel USB kebaca. Coba kabel/port USB lain. Cek di Device Manager apakah muncul sebagai COM port. |
| Dot gerak tapi game nggak respon | Cek tombol **Output: ON**, dan pastikan game baca controller XInput/Xbox. Tes dulu di `joy.cpl` (Set up USB game controllers). |
| Sering muncul peringatan LAG | Coba kabel USB lebih pendek/bagus, hindari USB hub, dan tutup aplikasi berat lain. Klik **💾 Simpan ke file** buat analisa `session.log`. |
| Axis kebalik / drift | Pakai panel Kalibrasi: Invert untuk kebalik, Deadzone untuk drift. |

---

## 📄 Lisensi & kredit

Berbasis logika decoding serial dari script asli `main.py`. Output gamepad pakai [`vgamepad`](https://github.com/yannbouteiller/vgamepad) (ViGEmBus).
