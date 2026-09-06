# 🎬 YouTube Transcripter

Paste a YouTube link, pick a Whisper model, get the transcript.
Everything runs **locally** on your machine inside Docker — no API keys, no cloud, no accounts.

Works the same on **Linux, Windows and macOS**.

- Downloads only the **audio** track with `yt-dlp` (fast, small)
- Transcribes with **Whisper** via [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper)
- Keeps a searchable **history** in a local SQLite database
- **Copy** the text or **download it as Markdown**, named after the video
- **One-command switch** between CPU and NVIDIA GPU
- **Starts by itself** every time you boot your computer

---

## Table of contents

1. [Requirements](#1-requirements)
2. [Quick start](#2-quick-start)
3. [Switching between CPU and GPU](#3-switching-between-cpu-and-gpu)
4. [GPU setup (NVIDIA)](#4-gpu-setup-nvidia)
5. [Autostart on boot](#5-autostart-on-boot)
6. [How to use the app](#6-how-to-use-the-app)
7. [Choosing a Whisper model](#7-choosing-a-whisper-model)
8. [Configuration](#8-configuration)
9. [Your data and backups](#9-your-data-and-backups)
10. [Everyday commands](#10-everyday-commands)
11. [Troubleshooting](#11-troubleshooting)
12. [Uninstall](#12-uninstall)
13. [Project layout](#13-project-layout)

---

## 1. Requirements

**Mandatory, all platforms**

| What | Minimum | How to check |
|---|---|---|
| Docker | Engine 24+ / Desktop 4.30+ | `docker --version` |
| Docker Compose | v2+ | `docker compose version` |
| Free disk space | ~5 GB (CPU) / ~12 GB (GPU) | — |
| RAM | 4 GB free | — |
| Internet | To download videos, and once per model | — |

> **You do not need Python, ffmpeg or Whisper installed on your machine.**
> Everything lives inside the container.

**Optional, for GPU acceleration**

| What | Notes |
|---|---|
| NVIDIA GPU | 4 GB+ VRAM recommended |
| NVIDIA driver | 550+ (`nvidia-smi`) |
| Extra setup | See [section 4](#4-gpu-setup-nvidia) |

<details>
<summary><b>Installing Docker — Windows</b></summary>

1. Download [**Docker Desktop for Windows**](https://www.docker.com/products/docker-desktop/).
2. During install, keep **"Use WSL 2 instead of Hyper-V"** ticked. This is required.
3. Reboot when asked, then launch Docker Desktop and wait for the whale icon in
   the tray to stop animating.
4. Open **PowerShell** and confirm:
   ```powershell
   docker --version
   docker compose version
   docker run --rm hello-world
   ```

If WSL 2 is missing, open PowerShell **as Administrator** and run:
```powershell
wsl --install
```
then reboot.
</details>

<details>
<summary><b>Installing Docker — Arch / CachyOS / Manjaro</b></summary>

```bash
sudo pacman -S docker docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
# Log out and back in so the group takes effect
docker run --rm hello-world
```
</details>

<details>
<summary><b>Installing Docker — Ubuntu / Debian</b></summary>

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
# Log out and back in
docker run --rm hello-world
```
</details>

<details>
<summary><b>Installing Docker — macOS</b></summary>

Install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
(pick the Apple Silicon or Intel build to match your machine), then:
```bash
docker run --rm hello-world
```
GPU acceleration is **not** available on macOS — the app runs on CPU.
</details>

---

## 2. Quick start

### 🐧 Linux / 🍎 macOS

```bash
cd youtube-transcripter
cp .env.example .env
docker compose up -d --build
```

### 🪟 Windows (PowerShell)

```powershell
cd youtube-transcripter
Copy-Item .env.example .env
docker compose up -d --build
```

> 🖱️ **Prefer not to use a terminal?** Once you have created `.env`, just
> **double-click `start.cmd`**. It starts the app and opens your browser.

### Then, on any platform

The first build takes **3–8 minutes** (it downloads Python, ffmpeg and the
libraries). Later starts take a couple of seconds.

👉 Open **<http://localhost:8501>**

Confirm it is healthy:
```
docker compose ps
```
You should see `youtube-transcripter` with status `Up (healthy)`.

> ⏳ **The first transcription is slower.** Whisper downloads the model you
> picked (0.5–3 GB) the first time you use it. It is cached in `./models/` and
> reused forever after.

---

## 3. Switching between CPU and GPU

The mode is stored in **one line** of your `.env` file:

```ini
COMPOSE_FILE=docker-compose.yml                            # CPU
COMPOSE_FILE=docker-compose.yml:docker-compose.gpu.yml     # NVIDIA GPU
```

Because Docker Compose reads that variable itself, **the command to start the
app is `docker compose up -d` in both modes** — you never have to remember
extra `-f` flags.

### The easy way

```bash
./mode.sh              # show the current mode and live runtime
./mode.sh gpu          # switch to GPU, rebuild, restart
./mode.sh cpu          # switch back to CPU, rebuild, restart
```

```powershell
.\mode.ps1             # show the current mode and live runtime
.\mode.ps1 gpu         # switch to GPU, rebuild, restart
.\mode.ps1 cpu         # switch back to CPU, rebuild, restart
```

Example output:
```
Current mode: cpu
Runtime reported by the app:
  CPU · int8
```

### The manual way

Edit `.env`, comment one line and uncomment the other, then:
```
docker compose up -d --build
```

### How to tell which mode is live

Look at the **Runtime** line in the app's sidebar:

| Sidebar shows | Meaning |
|---|---|
| 🔵 `CPU · int8` | Running on the processor |
| 🟢 `CUDA (GPU) · float16` | Running on your NVIDIA GPU |

> The GPU image is a separate ~5 GB build. The first `mode.sh gpu` will take a
> while. Switching back and forth afterwards is fast — both images are cached.

> 🛟 **Safe by design.** If you switch to GPU and something is wrong with the
> driver, the app does not crash — it prints *"GPU unavailable, falling back to
> CPU"* and transcribes on the processor anyway.

---

## 4. GPU setup (NVIDIA)

A GPU makes transcription roughly **5–15× faster**. Skip this section if you do
not have an NVIDIA card. macOS is CPU-only.

### 🪟 Windows

Docker Desktop already bundles the GPU plumbing — you only need the driver.

1. **Install/update the NVIDIA driver for Windows** (version 550+) from
   [nvidia.com/drivers](https://www.nvidia.com/download/index.aspx).
   Install it on **Windows**, not inside WSL.
2. **Confirm Docker Desktop uses the WSL 2 backend**:
   Settings → General → *Use the WSL 2 based engine* must be ticked.
3. **Verify Docker can see the GPU** (PowerShell):
   ```powershell
   docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
   ```
   If this prints your GPU, you are ready.
4. **Switch modes**:
   ```powershell
   .\mode.ps1 gpu
   ```

### 🐧 Linux

You need the NVIDIA Container Toolkit.

*Arch / CachyOS:*
```bash
sudo pacman -S nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

*Ubuntu / Debian:*
```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

Verify, then switch:
```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
./mode.sh gpu
```

---

## 5. Autostart on boot

**This is handled by Docker itself.** `docker-compose.yml` sets:

```yaml
restart: unless-stopped
```

Docker brings the container back automatically whenever the Docker daemon
starts — including after a reboot — unless you stopped it manually. There is
nothing to install for that part.

The only requirement is that **Docker itself starts with your machine**:

### 🪟 Windows

Open **Docker Desktop → Settings → General** and tick
**"Start Docker Desktop when you log in"**. Apply & restart.

That is genuinely all that is needed.

### 🐧 Linux

```bash
sudo systemctl enable --now docker.service
docker compose up -d
```

### 🍎 macOS

Docker Desktop → Settings → General → **"Start Docker Desktop when you log in"**.

### Optional extra layer

The commands above cover a normal reboot. They do **not** bring the app back if
you ran `docker compose down` at some point — Docker respects that as a
deliberate stop. If you want it to come back regardless, install the helper:

```bash
./deploy/install-autostart.sh                                          # Linux (systemd unit)
```
```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\install-autostart.ps1  # Windows (Scheduled Task)
```

Both read the CPU/GPU mode from your `.env`, so you never pass it twice.
Neither needs to be reinstalled when you change modes with `mode.sh`.

**Verify it worked**

```bash
systemctl status youtube-transcripter.service     # Linux
```
```powershell
Get-ScheduledTask -TaskName YouTubeTranscripter   # Windows
```

**Test it for real** — reboot, log in, wait ~1 minute, then open
<http://localhost:8501>.

**To remove the extra layer later**
```bash
./deploy/uninstall-autostart.sh
```
```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\uninstall-autostart.ps1
```

---

## 6. How to use the app

```
┌────────────────────┬──────────────────────────────────────────────┐
│  ⚙️  SETTINGS       │            🎬 YouTube Transcripter            │
│                    │       Paste a link. Get the words.           │
│  Whisper Model     │                                              │
│  [ small       ▾]  │  ┌──────────────────────────┐ ┌───────────┐  │
│  ~1.5GB Fast Good  │  │ https://youtube.com/...  │ │ Transcribe│  │
│                    │  └──────────────────────────┘ └───────────┘  │
│  Language          │                                              │
│  [ Auto-detect ▾]  │  ▓▓▓▓▓▓▓▓▓░░░░░░░  Transcribing…             │
│                    │                                              │
│  ☐ Force re-run    │  ┌────────────────────────────────────────┐  │
│  ──────────────    │  │ [thumb]  Video Title                   │  │
│  Runtime           │  │          Channel · 12:34               │  │
│  🟢 CUDA · float16 │  │          [small] [EN] [cuda] [842 words]│  │
│  ──────────────    │  └────────────────────────────────────────┘  │
│  📜 HISTORY         │  ┌────────────────────────────────────────┐  │
│  [ Search…       ] │  │ The transcription text appears here…   │  │
│   Video A          │  │                                        │  │
│   [Open]     [🗑]  │  └────────────────────────────────────────┘  │
│   Video B          │                                              │
│   [Open]     [🗑]  │   ┌──────────────┐   ┌────────────────────┐  │
│  🗑️ Clear history  │   │ 📋 Copy Text │   │ ⬇️ Download .md     │  │
└────────────────────┴───┴──────────────┴───┴────────────────────┴──┘
```

**The flow**

1. **Pick a model** in the sidebar. `small` is a good default; `turbo` is the
   best quality-per-second if you have a GPU. See [section 7](#7-choosing-a-whisper-model).
2. **Leave Language on `Auto-detect`** unless Whisper keeps guessing wrong.
3. **Paste the YouTube URL** and press **Transcribe** (or just hit Enter).
   All of these work:
   - `https://www.youtube.com/watch?v=VIDEO_ID`
   - `https://youtu.be/VIDEO_ID`
   - `https://www.youtube.com/shorts/VIDEO_ID`
   - even a bare `VIDEO_ID`
4. **Watch the progress bar**: *Reading video details → Downloading audio →
   Transcribing → Saving to history*.
5. **When it finishes**, the text appears with two buttons underneath:
   - **📋 Copy Text** — puts the whole transcript on your clipboard (turns green: *✓ Copied!*)
   - **⬇️ Download .md** — saves a Markdown file named after the video,
     e.g. `How-to-Build-a-REST-API-in-Python.md`
6. **Everything is saved.** Reopen any past transcription from the sidebar with
   **Open**, or remove it with **🗑**.

**Two useful behaviours**

- **Automatic caching.** Transcribing the same video with the same model again
  is *instant* — it is read straight from the database. The chip
  *"from history"* tells you when that happened.
- **Force re-transcribe.** Toggle it on to ignore the cache, e.g. after
  switching models or if the first run went badly.

---

## 7. Choosing a Whisper model

| Model | Download | Speed | Quality | Use it when |
|---|---|---|---|---|
| `tiny` | ~0.6 GB | Fastest | Basic | You just need the gist of a short clip |
| `base` | ~0.8 GB | Very fast | Decent | Clean audio, one clear speaker |
| `small` | ~1.5 GB | Fast | Good | **Default.** Good balance for most videos |
| `medium` | ~3.0 GB | Moderate | Very good | Accents, background noise, jargon |
| `large-v3` | ~5.0 GB | Slow | Best | Maximum accuracy, GPU strongly advised |
| `turbo` | ~3.0 GB | Very fast | Excellent | **Best pick on a GPU.** Near `large-v3` quality, much faster |

**Rules of thumb**

- On **CPU only**: stick to `tiny`, `base` or `small`. `medium` and above will
  be painfully slow.
- On a **GPU with 6 GB VRAM** (e.g. RTX 3050/4050): `turbo` is the sweet spot.
  `large-v3` fits but leaves little headroom.
- Models are downloaded **once** and cached in `./models/`. Going back to a
  model you used before is instant.

---

## 8. Configuration

All settings live in `.env`. Restart the container after changing it:
```
docker compose up -d
```

| Variable | Default | What it does |
|---|---|---|
| `COMPOSE_FILE` | `docker-compose.yml` | **CPU/GPU mode.** See [section 3](#3-switching-between-cpu-and-gpu) |
| `COMPOSE_PATH_SEPARATOR` | `:` | Keeps the mode line identical on Windows and Linux |
| `DB_PATH` | `/app/data/transcripts.db` | History database (path inside the container) |
| `MODELS_DIR` | `/app/models` | Whisper model cache |
| `DOWNLOADS_DIR` | `/app/downloads` | Temporary audio, deleted after each run |
| `WHISPER_DEVICE` | `auto` | `auto`, `cuda` or `cpu`. `auto` uses the GPU when available |
| `WHISPER_COMPUTE_TYPE` | `auto` | `auto`, `float16`, `int8_float16`, `int8`, `float32` |
| `DEFAULT_MODEL` | `small` | Model pre-selected in the sidebar |
| `WHISPER_BEAM_SIZE` | `5` | Higher = marginally better and slower. `1` is greedy and fastest |
| `WHISPER_VAD` | `true` | Voice Activity Detection — skips silence, usually faster and cleaner |
| `MAX_DURATION_MINUTES` | `180` | Refuses videos longer than this. Raise it for long podcasts |
| `HISTORY_LIMIT` | `50` | How many entries the sidebar lists |
| `UID` / `GID` | `1000` | Linux only — match the container user to your host user |

**Changing the port.** If `8501` is taken, edit `docker-compose.yml`:
```yaml
ports:
  - "9000:8501"     # app becomes available at http://localhost:9000
```

---

## 9. Your data and backups

| Folder | Contents | Back it up? |
|---|---|---|
| `./data/` | `transcripts.db` — every transcription you have made | ✅ **Yes** |
| `./models/` | Whisper weights | ❌ No, they re-download |
| `./downloads/` | Temporary audio, wiped after each run | ❌ No |

These are ordinary folders next to the project on **all platforms** — on
Windows you can open `data\` in Explorer like any other folder.

**Backup**
```bash
cp data/transcripts.db "backup-$(date +%F).db"
```
```powershell
Copy-Item data\transcripts.db "backup-$(Get-Date -Format yyyy-MM-dd).db"
```

**Inspect the database** (no need to install SQLite — use the container):
```
docker compose exec transcripter python -c "import sqlite3;print(*sqlite3.connect('/app/data/transcripts.db').execute('SELECT id,title,whisper_model,word_count,created_at FROM transcriptions ORDER BY created_at DESC LIMIT 10'),sep=chr(10))"
```

---

## 10. Everyday commands

The same everywhere. The CPU/GPU mode is already baked into `.env`, so these
never change.

```
docker compose up -d              # start (or apply .env changes)
docker compose down               # stop and remove the container
docker compose restart            # quick restart
docker compose ps                 # status and health
docker compose logs -f            # follow the logs live
docker compose logs --tail 100    # last 100 lines
docker compose up -d --build      # rebuild after changing the code
```

Mode switching:
```bash
./mode.sh                # Linux / macOS
```
```powershell
.\mode.ps1               # Windows
```

---

## 11. Troubleshooting

<details open>
<summary><b>🪟 Windows: "docker : The term 'docker' is not recognized"</b></summary>

Docker Desktop is not installed, or not running. Launch it from the Start menu
and wait until the whale icon in the system tray stops animating, then reopen
PowerShell.
</details>

<details>
<summary><b>🪟 Windows: ".\mode.ps1 cannot be loaded because running scripts is disabled"</b></summary>

That is the PowerShell execution policy. Either run it as a one-off:
```powershell
powershell -ExecutionPolicy Bypass -File .\mode.ps1 gpu
```
or allow local scripts permanently for your user:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
</details>

<details>
<summary><b>🪟 Windows: build fails with a weird "not found" or "invalid" error</b></summary>

Almost always **line endings**. If Git converted the project files to CRLF, the
Linux container cannot read them.

The included `.gitattributes` prevents this on a fresh clone. If you cloned
before it existed, fix it with:
```powershell
git config core.autocrlf false
git rm --cached -r .
git reset --hard
docker compose build --no-cache
```
</details>

<details>
<summary><b>Port 8501 is already in use</b></summary>

```bash
ss -tulpn | grep 8501            # Linux
```
```powershell
Get-NetTCPConnection -LocalPort 8501    # Windows
```
Either stop that process, or change the host port in `docker-compose.yml`
(see [section 8](#8-configuration)).
</details>

<details>
<summary><b>"CUDA out of memory" / "cuDNN error"</b></summary>

Your GPU does not have enough free VRAM for the chosen model.

1. Pick a smaller model (`turbo` instead of `large-v3`, or `small`).
2. Or lower the precision in `.env`:
   ```
   WHISPER_COMPUTE_TYPE=int8_float16
   ```
3. Or go back to CPU entirely:
   ```bash
   ./mode.sh cpu
   ```

The app already falls back to CPU on its own when the GPU cannot load the model
— you will see *"GPU unavailable, falling back to CPU"* in the status line.
</details>

<details>
<summary><b>The sidebar still says CPU after switching to GPU</b></summary>

Check, in order:

1. `./mode.sh` (or `.\mode.ps1`) — does it say `Current mode: gpu`?
2. `docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi` —
   does Docker see the card? If not, redo [section 4](#4-gpu-setup-nvidia).
3. `docker compose logs --tail 50` — look for a CUDA/cuDNN error near the end.
4. Make sure `WHISPER_DEVICE` in `.env` is `auto` or `cuda`, not `cpu`.
</details>

<details>
<summary><b>"This video is unavailable" / "Sign in to confirm you're not a bot"</b></summary>

YouTube throttles anonymous downloads sometimes.

1. Wait a few minutes and retry.
2. Make sure `yt-dlp` is current — it changes often as YouTube changes:
   ```
   docker compose build --no-cache
   docker compose up -d
   ```
3. Age-restricted and private videos cannot be downloaded anonymously.
</details>

<details>
<summary><b>Transcription is extremely slow</b></summary>

Check the **Runtime** line in the sidebar.

- 🔵 **CPU** — expect roughly 1–3× real time with `small`. Use `tiny`/`base`,
  or set up the GPU ([section 4](#4-gpu-setup-nvidia)).
- 🟢 **CUDA** — should be many times faster than real time. If it is not,
  confirm the GPU is actually busy with `nvidia-smi` while it runs.

Also: the very first run of a model includes its download. That is a one-off.
</details>

<details>
<summary><b>"No speech was detected in this video"</b></summary>

The audio is silent, music-only, or you forced the wrong language.
Set **Language** back to `Auto-detect` and try again.
</details>

<details>
<summary><b>The Copy button does not work</b></summary>

Browsers only allow clipboard access on secure origins. `http://localhost`
counts as secure, so it works there. If you reach the app through a LAN IP such
as `http://192.168.0.10:8501`, the button falls back to a legacy copy method —
and if that is blocked too, it turns red with *"✗ Press Ctrl+C"*. Select the
text manually, or use **Download .md** instead.
</details>

<details>
<summary><b>🐧 Linux: permission denied on data/ or models/</b></summary>

The container runs as UID 1000. If your host user has a different UID, add
yours to `.env`:
```bash
echo "UID=$(id -u)" >> .env
echo "GID=$(id -g)" >> .env
docker compose up -d --build
```
This does not apply to Windows or macOS — Docker Desktop handles it.
</details>

<details>
<summary><b>Nothing at all happens / the container keeps restarting</b></summary>

```
docker compose logs --tail 100
```
The traceback is almost always at the bottom. A clean rebuild fixes most odd
states:
```
docker compose down
docker compose build --no-cache
docker compose up -d
```
</details>

---

## 12. Uninstall

```bash
./deploy/uninstall-autostart.sh              # Linux, if you installed it
docker compose down
docker rmi youtube-transcripter:cpu youtube-transcripter:gpu
```
```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\uninstall-autostart.ps1
docker compose down
docker rmi youtube-transcripter:cpu youtube-transcripter:gpu
```

To also delete your transcriptions and cached models, remove the `data/`,
`models/` and `downloads/` folders.

---

## 13. Project layout

```
youtube-transcripter/
├── app/
│   ├── main.py                 Streamlit entrypoint
│   ├── config.py               Settings read from .env
│   ├── core/
│   │   ├── downloader.py       yt-dlp: metadata + audio extraction
│   │   ├── transcriber.py      faster-whisper, model cache, GPU fallback
│   │   ├── pipeline.py         Orchestrates the whole job
│   │   ├── exporter.py         Markdown export + safe filenames
│   │   └── errors.py           Errors the UI knows how to show
│   ├── db/
│   │   ├── database.py         Connection, schema, WAL, FTS5
│   │   ├── models.py           Dataclasses
│   │   └── repository.py       All SQL lives here
│   └── ui/
│       ├── styles.py           The red palette and page CSS
│       ├── sidebar.py          Model picker, options, runtime status
│       ├── result.py           Video card, transcript, action buttons
│       ├── history.py          Sidebar history with search
│       └── components.py       Clipboard button
├── .streamlit/config.toml      Streamlit theme and server settings
├── deploy/
│   ├── install-autostart.sh    Optional boot service (Linux)
│   ├── install-autostart.ps1   Optional logon task (Windows)
│   └── uninstall-autostart.*   Removes them
├── mode.sh / mode.ps1          Switch between CPU and GPU
├── start.cmd                   Double-click launcher (Windows)
├── data/  models/  downloads/  Persisted folders
├── Dockerfile                  CPU image
├── Dockerfile.gpu              CUDA image
├── docker-compose.yml          Base stack
├── docker-compose.gpu.yml      GPU override (activated via .env)
├── .gitattributes              Forces LF so Windows clones build correctly
└── .env.example                Copy to .env
```

---

## Credits

Built with [Streamlit](https://streamlit.io), [yt-dlp](https://github.com/yt-dlp/yt-dlp),
[faster-whisper](https://github.com/SYSTRAN/faster-whisper) and
[OpenAI Whisper](https://github.com/openai/whisper) models.

Transcribe only content you have the right to use.
