# 🛩️ DJI Mini → Xbox Controller

A Windows desktop app that turns a **DJI Mavic Mini remote** (DJI MR1SD25) into a **Virtual Xbox 360 Controller**. The remote is read over serial USB and mapped to a virtual gamepad via [`vgamepad`](https://github.com/yannbouteiller/vgamepad) + [ViGEmBus](https://github.com/nefarius/ViGEmBus) — so your DJI sticks show up like a normal controller in any game or simulator.

Built on top of the original CLI script (`main.py`), with a UI added: auto port detection, live analog visualization, full calibration, and a log panel with lag detection.

---

## ▶️ Quick Start (Windows)

> ⚠️ Install **ViGEmBus** first (one time only): https://github.com/nefarius/ViGEmBus/releases

**1. Setup (first time):**
```bash
git clone https://github.com/firdanmanggalap/djiminicontroller.git
cd djiminicontroller
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**2. Run (every time you use it):**
```bash
cd djiminicontroller
.venv\Scripts\activate
python app.py
```

3. **Plug in the DJI remote** via USB → the app finds and connects automatically (the status chip at the top-right turns green: **"● Connected — COMx"**). Open your game/simulator and the controller is recognized as an Xbox 360 pad.

> If you use **PowerShell** and hit an execution-policy error on `activate`, run: `Set-ExecutionPolicy -Scope Process RemoteSigned` and try again — or just use Command Prompt (cmd).
> ViGEmBus not installed yet? The app still opens but shows a warning dialog, and gamepad output stays off until ViGEmBus is installed.

---

## ✨ Features

| | Feature |
|---|---|
| 🔌 | **Auto-detect + auto-reconnect** — scans ports on its own, identifies the DJI remote by probing, connects automatically, and reconnects if the cable is unplugged. No need to type a COM port. |
| 🕹️ | **Live analog visualization** — two sticks (left Throttle/Yaw, right Pitch/Roll) + a camera-dial bar. The dot follows the **physical** stick position, so you can verify the reading is correct. |
| 🔄 | **Per-axis invert** — toggle right in the UI. Invert only affects the game output; the display still shows the physical direction. |
| 🎯 | **Full calibration** — deadzone, center trim, and range/sensitivity per axis. Auto-saved to `config.json`. Includes a Reset button. |
| 🎮 | **Output ON/OFF** — stop/resume sending to the virtual gamepad without closing the app. |
| 📊 | **Live log + lag detection** — Hz/interval indicator, an automatic warning when the inter-packet gap spikes (lag) plus a dropped-packet estimate, and Pause / Clear / Save-to-file buttons. |

---

## 📋 Requirements

### Hardware
- **DJI Mavic Mini remote (DJI MR1SD25)** + a USB cable to the PC.
- The remote powered on.

### Software (Windows)
- **Windows 10 / 11**
- **Python 3.10+** — make sure "Add Python to PATH" is checked during install.
- **ViGEmBus driver** — the system driver used to create the virtual Xbox controller.
  Download & install the latest release: **https://github.com/nefarius/ViGEmBus/releases** (grab the latest `.exe` installer, install, restart if prompted).
- **Python packages** (see `requirements.txt`):

  | Package | Purpose |
  |---|---|
  | `PySide6` | desktop UI (Qt) |
  | `pyserial` | read serial port + scan ports |
  | `vgamepad` | output to a Virtual Xbox 360 (requires ViGEmBus) |
  | `pytest` | run the tests (optional, for development) |

> **Note:** This app is **Windows-only** because `vgamepad`/ViGEmBus only run on Windows. On Linux/macOS only the tests run — the GUI and gamepad output do not.

---

## 🖥️ UI Guide

- **Header** — title, a `⟳ Hz · interval ms · drop` indicator, connection status, and an **Output: ON/OFF** button.
- **Left panel (Live)** — two analog pads (the dot tracks the physical stick) + numeric values, plus a **camera dial → Right Trigger** bar.
- **Right panel (Calibration)** — per axis: **Invert** (checkbox), **Deadzone** (0–30%), **Trim** (shift the center point), **Range** (0.5×–1.5× sensitivity). Everything auto-saves. There's a **Reset** button.
- **Bottom panel (Log)** — live log (scan/connect, rate, lag warnings, reconnect). **Pause**, **Clear**, and **💾 Save to file** (`session.log`) buttons.

### Calibration tips
- **Dot moves opposite to the physical stick in-game?** → toggle that axis's **Invert**.
- **Stick drifts when released?** → raise that axis's **Deadzone**.
- **Center point isn't quite neutral?** → adjust **Trim**.
- **Want more/less sensitivity?** → adjust **Range**.

Settings are stored in `config.json` (in the app folder) and reload automatically next time you open it.

---

## 🧠 How it works (brief)

```
serial_link.py (QThread)   read 38-byte frame from remote → parse 5 axes → detect lag → auto-reconnect
        │ Qt signals (rawAxes / status / stats / log)
        ▼
main_window.py             mapping.py: raw → trim → deadzone → range → invert → Xbox int16
        ├──► AnalogStick    show physical position (live dot)
        └──► gamepad_out.py  vgamepad.VX360Gamepad → Virtual Xbox 360 (output respects invert)
config.py ↔ config.json    save/load calibration · logger.py → log panel + session.log
```

The DJI remote is read at **115200 baud**; the app sends a repeated *ping* packet and waits for a **38-byte** reply containing 4 stick values + 1 camera dial (little-endian). Port detection works by **probing** (send the ping, check for a 38-byte reply) — so it doesn't depend on VID/PID, and it connects regardless of the COM number.

---

## 🧪 Development & Testing

All core logic (parsing, mapping, config, lag detection, logging) is decoupled from I/O and the UI, so it can be tested without hardware (and without `vgamepad`/Windows):

```bash
python -m pytest -q
```

41 unit tests cover `protocol`, `mapping`, `config`, `lag_detector`, `logger`, `gamepad_out`, `serial_probe`, the widget, and the `main_window` wiring (using a fake serial + injected gamepad). The serial/gamepad/GUI paths that need hardware are verified manually on Windows.

Structure:
```
app.py                  entry point
dji_xbox/
  protocol.py           constants + packet parsing (pure)
  mapping.py            calibration raw → Xbox int16 (pure)
  config.py             load/save config.json
  lag_detector.py       Hz rate + lag detection (pure)
  logger.py             log buffer + optional file
  gamepad_out.py        vgamepad wrapper
  serial_link.py        QThread serial reader + reconnect
  widgets/analog_stick.py   custom analog widget
  main_window.py        main UI
tests/                  unit tests
main.py                 original CLI script (reference)
```

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| "ViGEmBus not ready" dialog / failed to create the virtual pad | ViGEmBus isn't installed — install it from [releases](https://github.com/nefarius/ViGEmBus/releases), restart, and run again. |
| Status stuck at "Searching for remote…" | Make sure the remote is on and the USB cable works. Try a different cable/port. Check Device Manager to confirm it shows up as a COM port. |
| Dot moves but the game doesn't respond | Check the **Output: ON** button, and make sure the game reads XInput/Xbox controllers. Test first in `joy.cpl` (Set up USB game controllers). |
| Frequent LAG warnings | Try a shorter/better USB cable, avoid USB hubs, and close other heavy apps. Click **💾 Save to file** to analyze `session.log`. |
| Axis inverted / drifting | Use the Calibration panel: Invert for direction, Deadzone for drift. |

---

## 📄 License & credits

Based on the serial-decoding logic from the original `main.py` script. Gamepad output uses [`vgamepad`](https://github.com/yannbouteiller/vgamepad) (ViGEmBus).
