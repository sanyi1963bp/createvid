# WAN2_2 – hosszú videó helyi géppel

Egy képből és egy rövid leírásból **perces videót** készít, teljesen a saját gépeden, felhő és előfizetés nélkül.

- **Wan 2.2 I2V** (képből videó) + **Stable Video Infinity 2.0 Pro** (a klipek varrat nélküli láncolása)
- 5 másodperces klipekből építkezik; minden klip folytatja az előzőt, a szereplő és a stílus végig megmarad
- Magyarul is megadhatod, mi történjen: a helyi AI (Ollama) megírja belőle a klipenkénti angol promptokat
- Egyszerű varázsló: kép ráhúzása → téma → hossz → indítás

## Gépigény

| | Minimum | Tesztelve |
|---|---|---|
| Rendszer | Windows 10/11 | Windows 11 |
| GPU | NVIDIA, 12 GB VRAM | RTX 5070 Ti, 16 GB |
| RAM | 32 GB | 64 GB |
| Szabad hely | ~40 GB | |

Sebesség (RTX 5070 Ti, gyors mód): **5 mp videó ≈ 2,5 perc**, 1 perc videó ≈ 30 perc. Minőségi módban kb. kétszer lassabb.

## Telepítés

1. Töltsd le / klónozd ezt a mappát egy olyan meghajtóra, ahol van ~40 GB hely.
2. Kattints duplán a **`telepito.bat`**-ra. Letölti:
   - a ComfyUI-t (hordozható változat, ~2 GB, nem kell hozzá külön Python),
   - a két kiegészítőt (ComfyUI-GGUF, ComfyUI-KJNodes, rögzített verzióval),
   - a modelleket (~31 GB, Hugging Face-ről – ez a leghosszabb).

   Ha megszakad, csak futtasd újra: ott folytatja, ahol abbahagyta.
3. A telepítő ellenőrzi az **ffmpeg**-et (kötelező, felajánlja a telepítését) és az **Ollamát** (nem kötelező).

## Használat

**Video_keszito.bat** – dupla kattintás, és a varázsló végigvezet:

1. **Kezdőkép** – húzd rá a képet az ablakra, Enter
2. **Mi történjen** – pár mondat, magyarul is lehet
3. **Hossz** másodpercben
4. **Mód** – gyors vagy minőségi

Ezután az AI megírja a promptokat; megnézheted, újraírathatod vagy egy-egy sort átírhatsz, majd Enter és indul.
A kész videó a `kimenet\` mappába kerül és magától megnyílik. A feladat a `feladatok\` mappába mentődik:
újrafuttatáshoz húzd a json-t a **Hosszu_video.bat**-ra.

A varázsló magától elindítja a ComfyUI-t, ha nem fut (külön ablakban; a végén bezárhatod).

### Feladatfájl kézzel

```json
{
  "kep": "pelda_kep.jpg",
  "promptok": ["első 5 mp leírása angolul", "második 5 mp", "..."],
  "cfg": 1.0,
  "seed": 12345
}
```

További beállítások (alapértékek a `hosszu_video.py` elején): `klipek_szama`, `terulet` (képpont/kocka, alap 832×480),
`lepesek`, `lightx2v_high`, `lightx2v_low`, `motion_latent`, `fps`.

## Tippek

- Egyszerű, folyamatos cselekmény működik legjobban (séta, fordulás, odanyúlás, tánc, szél, felhők).
- A kezdőkép rögzíti a külsőt és a stílust; a prompt a mozgást írja le.
- Ha a prompt ellentmond a képnek, a modell inkább a promptot követi, a kép stílusát megtartva.
- Más eredményhez írd át a `seed`-et a feladatfájlban.
- Generálás közben ne fusson más nagy GPU-program.

## Fájlok

| Fájl | Mire jó |
|---|---|
| `Video_keszito.bat` / `video_keszito.py` | Varázsló |
| `Hosszu_video.bat` / `hosszu_video.py` | A motor; feladatfájlból generál |
| `ComfyUI_inditas.bat` | A ComfyUI kézi indítása (böngészőben: http://127.0.0.1:8188) |
| `telepito.bat` / `telepito.ps1` | Telepítő |
| `modellek.txt` | A letöltendő modellek listája |
| `pelda_feladat.json` + `pelda_kep.jpg` | Példa (Munkácsy Mihály: Golgota, 1884 – közkincs) |

## Hogyan működik

Klipenként (81 kocka ≈ 5 mp) a ComfyUI API-ján fut egy gráf: a Wan 2.2 két modellje (HighNoise: nagy mozgások,
LowNoise: részletek) a LightX2V gyorsító LoRA-val 6 lépésben generál. Az SVI 2.0 Pro LoRA és a `WanImageToVideoSVIPro`
node minden klipnek megadja a kezdőképet (horgony) és az előző klip utolsó latensét, így a mozgás folytatódik.
A végén az ffmpeg fűzi össze a kockákat (a második kliptől az első, ismétlődő kocka kimarad).

## Források és licencek

- [ComfyUI](https://github.com/Comfy-Org/ComfyUI) – GPL-3.0
- [Wan 2.2](https://github.com/Wan-Video/Wan2.2) – Apache-2.0; GGUF: [QuantStack](https://huggingface.co/QuantStack/Wan2.2-I2V-A14B-GGUF)
- [Stable Video Infinity](https://github.com/vita-epfl/Stable-Video-Infinity) (EPFL VITA) – lásd a projekt licencét
- [LightX2V](https://github.com/ModelTC/LightX2V); LoRA-k: [Kijai/WanVideo_comfy](https://huggingface.co/Kijai/WanVideo_comfy)
- [ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF), [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes)

A modelleket és a ComfyUI-t ez a repó nem tartalmazza; a telepítő a hivatalos helyükről tölti le őket.
A saját szkriptek licence: MIT (lásd `LICENSE`).
