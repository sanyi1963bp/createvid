# Fájlok leírása / File reference

- [Magyarul](#magyarul)
- [English](#english)

---

## Magyarul

### Indítófájlok (dupla kattintással)

| Fájl | Feladat és szerep |
|---|---|
| `telepito.bat` | **Telepítés.** Elindítja a `telepito.ps1`-et Windows PowerShellben (a végrehajtási szabályzat megkerülésével), és a végén nyitva hagyja az ablakot, hogy látszódjon az eredmény. Paramétert továbbad (pl. `-NemKerdez`). |
| `Video_keszito.bat` | **Videókészítés – a fő belépési pont.** Elindítja a `video_keszito.py` varázslót a ComfyUI saját (beágyazott) Pythonjával, UTF-8 kiírással. |
| `Hosszu_video.bat` | **Kész feladat újrafuttatása.** Ha egy feladatfájlt (`.json`) ráhúzol, azt generálja le a `hosszu_video.py`-val; ha üresen indítod, a `pelda_feladat.json`-t. A ComfyUI-nak közben futnia kell. |
| `ComfyUI_inditas.bat` | **A ComfyUI szerver kézi indítása** a `ComfyUI_windows_portable` mappából. A varázsló szükség esetén magától is meghívja. Böngészőben: http://127.0.0.1:8188 |

### Programfájlok

| Fájl | Feladat és szerep |
|---|---|
| `video_keszito.py` | **A varázsló.** Sorban megkérdezi: kezdőkép (ráhúzással), mi történjen (magyarul is), hossz másodpercben, gyors vagy minőségi mód. Kiszámolja a klipek számát (1 klip = 81 kocka ≈ 5 mp). Felszabadítja a ComfyUI által foglalt videómemóriát, majd a helyi **Ollama** modellel (alapból `gemma4:12b`, ha nincs, másik telepített modell) a kép és a téma alapján megíratja a klipenkénti angol promptokat. Ezeket megmutatja; újraírathatók, soronként átírhatók, vagy Ollama nélkül kézzel is beírhatók. A feladatot elmenti a `feladatok\` mappába, megvárja/elindítja a ComfyUI-t, lefuttatja a `hosszu_video.py`-t, a végén megnyitja a kész videót. |
| `hosszu_video.py` | **A motor.** Egy feladatfájlból (`.json`) dolgozik. Klipenként felépít egy ComfyUI API-gráfot: két GGUF Wan 2.2 modell (HighNoise: nagy mozgások, LowNoise: részletek), SVI 2.0 Pro és LightX2V LoRA-k, `WanImageToVideoSVIPro` node, kétlépcsős `KSamplerAdvanced` mintavételezés. Minden klip megkapja a kezdőképet (horgony – ettől marad ugyanaz a szereplő) és az előző klip utolsó latensét (ettől folytatódik a mozgás); a latenst `SaveLatent` → `input\` mappa → `LoadLatent` úton adja tovább. Kiírja a haladást és a hátralévő időt. A végén az **ffmpeg** egy mp4-be fűzi a kockákat (a 2. kliptől az első, ismétlődő kocka kimarad), és a beállításokat (seed, méret) egy json-ba menti a videó mellé. Az alapértelmezett beállítások a fájl elején, az `ALAPERTELMEZES` szótárban vannak. |
| `telepito.ps1` | **A telepítő logikája.** Újraindítható: ami megvan, kihagyja, a félbeszakadt letöltést folytatja. Lépései: (1) GPU és szabad hely ellenőrzése; (2) a ComfyUI hordozható változatának letöltése és kicsomagolása (ha nincs 7-Zip, letölti a `7zr.exe`-t); (3) a ComfyUI-GGUF és ComfyUI-KJNodes kiegészítők letöltése rögzített commitról, Python-csomagjaik telepítése; (4) az `extra_model_paths.yaml` legenerálása a sablonból; (5) a modellek letöltése a `modellek.txt` alapján, méret-ellenőrzéssel; (6) ffmpeg ellenőrzése, szükség esetén telepítése winget-tel; (7) Ollama és a `gemma4:12b` ellenőrzése (nem kötelező). UTF-8 BOM-mal mentve, hogy a régi Windows PowerShell is helyesen olvassa az ékezeteket. |

### Adat- és beállítófájlok

| Fájl | Feladat és szerep |
|---|---|
| `modellek.txt` | **A letöltendő modellek listája** (~31 GB): soronként `almappa \| pontos méret bájtban \| URL`. A telepítő ebből dolgozik; a méret alapján dönti el, hogy egy fájl kész-e. Modellcseréhez (pl. más kvantálás) elég ezt és a `hosszu_video.py` modellneveit átírni. |
| `extra_model_paths.yaml.minta` | **Sablon a modellmappához.** A telepítő a helyőrzőt a `_modellek` mappa tényleges útvonalára cseréli, és `ComfyUI_windows_portable\ComfyUI\extra_model_paths.yaml` néven menti. Így a modellek a ComfyUI-tól külön mappában vannak, és a projekt bármelyik meghajtóról működik. |
| `pelda_feladat.json` | **Minta feladatfájl:** kezdőkép + 3 klipnyi angol prompt (kb. 15 mp). Bármelyik `hosszu_video.py`-beállítás felülírható benne (pl. `cfg`, `seed`, `klipek_szama`). |
| `pelda_kep.jpg` | **Mintakép** a példához: Munkácsy Mihály: Golgota (1884), közkincs, 1600 px szélesre kicsinyítve. |

### Dokumentáció és git

| Fájl | Feladat és szerep |
|---|---|
| `README.md` | **Leírás:** mi ez, gépigény, telepítés, használat, a feladatfájl formátuma, tippek, működés, források és licencek. |
| `FAJLOK_FILES.md` | Ez a fájl: minden fájl feladata magyarul és angolul. |
| `TELEPITOKESZLET.md` | **Fejlesztői jegyzet:** mi kerül a repóba és mi nem, mit tölt le a telepítő, rögzített verziók. |
| `LICENSE` | MIT licenc a saját szkriptekre. (A ComfyUI és a modellek saját licence érvényes, ezeket a repó nem tartalmazza.) |
| `.gitignore` | Kizárja a gitből a letöltött programot és modelleket, a kimenetet, a saját feladatokat, a naplókat és a képeket (a `pelda_kep.jpg` kivételével). |
| `.gitattributes` | A `.bat` és `.ps1` fájlok mindig Windows-sorvéggel (CRLF) töltődjenek le, különben a parancsfájlok hibázhatnak. A `.jpg` bináris. |

### Futás közben keletkező mappák (nincsenek a repóban)

| Mappa | Tartalom |
|---|---|
| `ComfyUI_windows_portable\` | A ComfyUI beágyazott Pythonnal és a kiegészítőkkel (~2,5 GB). A generált nyers kockák és latensek az `output\`, az átadott képek és latensek az `input\` almappájába kerülnek. |
| `_modellek\` | A modellek (~31 GB): `diffusion_models`, `text_encoders`, `vae`, `loras`. |
| `_letoltes\` | Ideiglenes letöltések (pl. a ComfyUI 7z csomagja); telepítés után törölhető. |
| `feladatok\` | A varázsló által mentett feladatfájlok; újrafuttathatók a `Hosszu_video.bat`-tal. |
| `kimenet\` | A kész videók (`nev_datum.mp4`) és mellettük a használt beállítások (`.json`). |
| `ffmpeg\` | Nem kötelező: ide tehető egy `ffmpeg.exe`, ha nincs a rendszerben. |

---

## English

### Launchers (double-click)

| File | Purpose and role |
|---|---|
| `telepito.bat` | **Install.** Runs `telepito.ps1` in Windows PowerShell (bypassing the execution policy) and keeps the window open so the result stays visible. Passes arguments through (e.g. `-NemKerdez` = no questions). |
| `Video_keszito.bat` | **Make a video – the main entry point.** Starts the `video_keszito.py` wizard with ComfyUI's embedded Python and UTF-8 console output. |
| `Hosszu_video.bat` | **Re-run a saved job.** Drop a job file (`.json`) on it to render it with `hosszu_video.py`; started empty, it renders `pelda_feladat.json`. ComfyUI must be running. |
| `ComfyUI_inditas.bat` | **Starts the ComfyUI server manually** from `ComfyUI_windows_portable`. The wizard calls it automatically when needed. Browser UI: http://127.0.0.1:8188 |

### Program files

| File | Purpose and role |
|---|---|
| `video_keszito.py` | **The wizard.** Asks in turn for: start image (drag and drop), what should happen (any language, e.g. Hungarian), length in seconds, fast or quality mode. Computes the number of clips (1 clip = 81 frames ≈ 5 s). Frees ComfyUI's VRAM, then has a local **Ollama** model (default `gemma4:12b`, otherwise another installed model) write one English prompt per clip from the image and the topic. Shows them; they can be regenerated, edited line by line, or typed manually without Ollama. Saves the job to `feladatok\`, waits for / starts ComfyUI, runs `hosszu_video.py`, and opens the finished video. |
| `hosszu_video.py` | **The engine.** Works from a job file (`.json`). For each clip it builds a ComfyUI API graph: two GGUF Wan 2.2 models (HighNoise: large motion, LowNoise: detail), SVI 2.0 Pro and LightX2V LoRAs, the `WanImageToVideoSVIPro` node and two-stage `KSamplerAdvanced` sampling. Every clip receives the start image (anchor – keeps the subject consistent) and the last latent of the previous clip (continues the motion); the latent is passed via `SaveLatent` → `input\` folder → `LoadLatent`. Prints progress and time remaining. Finally **ffmpeg** joins the frames into one mp4 (from the 2nd clip on, the first, duplicated frame is dropped) and the settings used (seed, size) are saved as a json next to the video. Defaults live in the `ALAPERTELMEZES` dictionary at the top of the file. |
| `telepito.ps1` | **The installer logic.** Restartable: skips what already exists and resumes interrupted downloads. Steps: (1) check GPU and free disk space; (2) download and extract the portable ComfyUI (fetches `7zr.exe` if 7-Zip is missing); (3) download the ComfyUI-GGUF and ComfyUI-KJNodes extensions at pinned commits and install their Python packages; (4) generate `extra_model_paths.yaml` from the template; (5) download the models listed in `modellek.txt` with size verification; (6) check ffmpeg, optionally install it via winget; (7) check Ollama and `gemma4:12b` (optional). Saved with a UTF-8 BOM so legacy Windows PowerShell reads the accented characters correctly. |

### Data and configuration files

| File | Purpose and role |
|---|---|
| `modellek.txt` | **List of models to download** (~31 GB): one per line, `subfolder \| exact size in bytes \| URL`. The installer uses the size to decide whether a file is complete. To swap models (e.g. another quantization) edit this and the model names in `hosszu_video.py`. |
| `extra_model_paths.yaml.minta` | **Template for the model folder.** The installer replaces the placeholder with the real path of `_modellek` and saves it as `ComfyUI_windows_portable\ComfyUI\extra_model_paths.yaml`. Models stay outside ComfyUI, and the project works from any drive. |
| `pelda_feladat.json` | **Example job:** start image + 3 English clip prompts (~15 s). Any `hosszu_video.py` setting can be overridden here (e.g. `cfg`, `seed`, `klipek_szama` = number of clips). |
| `pelda_kep.jpg` | **Example image:** Mihály Munkácsy, *Golgotha* (1884), public domain, resized to 1600 px wide. |

### Documentation and git

| File | Purpose and role |
|---|---|
| `README.md` | **Description** (Hungarian): what it is, requirements, install, usage, job file format, tips, how it works, sources and licenses. |
| `FAJLOK_FILES.md` | This file: the role of every file, in Hungarian and English. |
| `TELEPITOKESZLET.md` | **Developer notes** (Hungarian): what goes into the repo and what doesn't, what the installer downloads, pinned versions. |
| `LICENSE` | MIT license for the project's own scripts. (ComfyUI and the models keep their own licenses and are not included.) |
| `.gitignore` | Keeps the downloaded program and models, outputs, personal jobs, logs and images (except `pelda_kep.jpg`) out of git. |
| `.gitattributes` | Forces Windows line endings (CRLF) for `.bat` and `.ps1`, otherwise the scripts may fail; marks `.jpg` as binary. |

### Folders created at runtime (not in the repo)

| Folder | Contents |
|---|---|
| `ComfyUI_windows_portable\` | ComfyUI with embedded Python and extensions (~2.5 GB). Raw frames and latents go to its `output\`, images and latents handed over go to `input\`. |
| `_modellek\` | The models (~31 GB): `diffusion_models`, `text_encoders`, `vae`, `loras`. |
| `_letoltes\` | Temporary downloads (e.g. the ComfyUI 7z archive); can be deleted after installation. |
| `feladatok\` | Job files saved by the wizard; re-run them with `Hosszu_video.bat`. |
| `kimenet\` | Finished videos (`name_date.mp4`) with the settings used (`.json`) next to them. |
| `ffmpeg\` | Optional: put an `ffmpeg.exe` here if it is not installed system-wide. |
