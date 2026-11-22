# WAN2_2 – telepítőkészlet tartalma (GitHub)

A gitre csak a **saját, kicsi fájlok** kerülnek (pár tíz KB). A ComfyUI-t (~2 GB) és a modelleket (~31 GB)
a telepítő tölti le a hivatalos helyükről, így a repó kicsi marad, és nem terjesztünk mások modelljeit.

## 1. A repóba kerül

| Fájl | Állapot | Mire jó |
|---|---|---|
| `video_keszito.py` | ✅ kész | Varázsló: kép, téma, hossz, mód → promptok (Ollama) → generálás |
| `hosszu_video.py` | ✅ kész | A motor: klipenként hívja a ComfyUI-t, láncolja a latenseket, ffmpeg-gel összefűz |
| `Video_keszito.bat` | ✅ kész | A varázsló indítása dupla kattintással |
| `Hosszu_video.bat` | ✅ kész | Kész feladat (json) újrafuttatása: rá kell húzni a json-t |
| `ComfyUI_inditas.bat` | ✅ kész | A ComfyUI szerver indítása |
| `pelda_feladat.json` | ✅ kész | Minta feladatfájl a `pelda_kep.jpg`-hez |
| `pelda_kep.png` | ✅ kész (Munkácsy: Golgota, közkincs) | Jogtiszta mintakép a próbához (a mostani kezdőképek nem kerülnek fel) |
| `telepito.bat` | ✅ kész | Egy kattintásos telepítés: indítja a `telepito.ps1`-et |
| `telepito.ps1` | ✅ kész | ComfyUI letöltése és kicsomagolása, custom node-ok rögzített verzióval, pip csomagok, modellek letöltése (folytatható), `extra_model_paths.yaml` legenerálása, ffmpeg és Ollama ellenőrzése |
| `modellek.txt` | ✅ kész | A letöltendő modellek listája (URL + célmappa + méret), a telepítő ebből dolgozik |
| `extra_model_paths.yaml.minta` | ✅ kész | Sablon; a telepítő írja be a tényleges útvonalat (most fixen `H:\...` van benne) |
| `README.md` | ✅ kész | Mi ez, gépigény, telepítés, használat, tippek, források és licencek |
| `.gitignore` | ✅ kész | Lásd a 2. pontot |
| `LICENSE` | ✅ MIT | pl. MIT a saját szkriptekre |

## 2. NEM kerül a repóba (`.gitignore`)

| Mappa / fájl | Méret | Miért nem |
|---|---|---|
| `ComfyUI_windows_portable/` | ~2,5 GB | A telepítő tölti le (Comfy-Org kiadás) |
| `_modellek/` | ~31 GB | A telepítő tölti le (Hugging Face) |
| `_letoltes/` | ~2 GB | Ideiglenes letöltések |
| `kimenet/` | változó | Elkészült videók |
| `feladatok/` | kicsi | A saját feladataid (személyes képútvonalak vannak benne) |
| `*.log`, `*_log.txt`, `comfy_log.txt` | kicsi | Naplók |
| saját képek (`kezdokep.png`, `_kezdokep.png`, `Munkácsy_Golgota.jpg`, `fortepan_315333.jpg`) | ~16 MB | Saját vagy idegen kép, jogi okból se tegyük fel |
| `proba_gyors.json` | kicsi | Belső teszt |

## 3. Amit a telepítő letölt

**Program**
- ComfyUI Windows portable **v0.46.0** (nvidia, ~2,1 GB): github.com/Comfy-Org/ComfyUI/releases
- Custom node-ok, a most bevált verzióra rögzítve:
  - ComfyUI-GGUF `6ea2651` (city96)
  - ComfyUI-KJNodes `aa2b5ea` (kijai) – ebben van a `WanImageToVideoSVIPro`
  - ComfyUI-VideoHelperSuite `4d907be` (Kosinkadink) – opcionális
  - ComfyUI-Manager `2dd2f10` – opcionális

**Modellek (~31 GB, `_modellek/` alá)**

| Almappa | Fájl | Méret | Forrás (HF) |
|---|---|---|---|
| diffusion_models | Wan2.2-I2V-A14B-HighNoise-Q5_K_M.gguf | 10,8 GB | QuantStack/Wan2.2-I2V-A14B-GGUF |
| diffusion_models | Wan2.2-I2V-A14B-LowNoise-Q5_K_M.gguf | 10,8 GB | QuantStack/Wan2.2-I2V-A14B-GGUF |
| text_encoders | umt5_xxl_fp8_e4m3fn_scaled.safetensors | 6,7 GB | Comfy-Org/Wan_2.1_ComfyUI_repackaged |
| vae | wan_2.1_vae.safetensors | 0,25 GB | Comfy-Org/Wan_2.2_ComfyUI_Repackaged |
| loras | SVI_v2_PRO_Wan2.2-I2V-A14B_HIGH_lora_rank_128_fp16.safetensors | 1,2 GB | Kijai/WanVideo_comfy |
| loras | SVI_v2_PRO_Wan2.2-I2V-A14B_LOW_lora_rank_128_fp16.safetensors | 1,2 GB | Kijai/WanVideo_comfy |
| loras | Wan_2_2_I2V_A14B_HIGH_lightx2v_4step_lora_260412_rank_64_fp16.safetensors | 0,6 GB | Kijai/WanVideo_comfy |
| loras | Wan_2_2_I2V_A14B_LOW_lightx2v_4step_lora_260412_rank_64_fp16.safetensors | 0,6 GB | Kijai/WanVideo_comfy |

**Külső függőségek (csak ellenőrzi, telepíteni javasolja)**
- **ffmpeg** a PATH-on: kötelező az összefűzéshez (`winget install ffmpeg`)
- **Ollama + gemma4:12b** (~7,6 GB): opcionális, ez írja a promptokat; nélküle a varázsló kézi promptot kér

## 4. Gépigény (a README-be)
- Windows 10/11, NVIDIA GPU legalább 12 GB VRAM-mal (tesztelve: RTX 5070 Ti 16 GB), 32+ GB RAM (tesztelve: 64 GB)
- ~40 GB szabad hely
- Sebesség (5070 Ti, gyors mód): 5 mp videó ≈ 2,5 perc → 1 perc videó ≈ 30 perc

## 5. Felrakás előtt még javítandó a kódban
- `hosszu_video.py`: az ffmpeg elérési útja legyen állítható (vagy a telepítő tegye a mappába).
- `video_keszito.py`: ha a `gemma4:12b` nincs meg, ajánljon fel másik telepített modellt.
- Mappaneveket ne rögzítsünk a kódban (most is relatív, ez rendben van), csak a yaml sablonban.
