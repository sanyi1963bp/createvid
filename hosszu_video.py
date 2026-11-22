"""
Hosszú videó Wan 2.2 + Stable Video Infinity 2.0 Pro-val, helyi ComfyUI-n keresztül.

Működés: egy kezdőképből és egy prompt-listából klipenként (81 kocka ≈ 5 mp)
generál. Minden új klip megkapja a kezdőképet (horgony) és az előző klip utolsó
latensét, így a jelenet folytatódik. A végén ffmpeg fűzi össze egy mp4-be.

Használat (a ComfyUI-nak futnia kell: ComfyUI_inditas.bat):
    python hosszu_video.py feladat.json
"""
import json, os, sys, time, shutil, random, subprocess, urllib.request, urllib.error
from pathlib import Path

ALAP = Path(__file__).resolve().parent
COMFY = ALAP / "ComfyUI_windows_portable" / "ComfyUI"
SERVER = "http://127.0.0.1:8188"

ALAPERTELMEZES = {
    "kep": "kezdokep.png",
    "promptok": ["A person walks slowly through a sunny park, camera follows."],
    "negativ": "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走",
    "klipek_szama": None,          # None = ahány prompt van; ha több, az utolsó prompt ismétlődik
    "terulet": 832 * 480,          # képpont/kocka; a képarányt a kezdőkép adja
    "kocka_per_klip": 81,
    "fps": 16,
    "lepesek": 6,
    "valtas_lepes": 3,             # eddig a lépésig a HIGH, utána a LOW modell dolgozik
    "cfg": 1.0,                    # 1.0 = gyors (negatív prompt nem hat); SVI ajánlás 1.5: jobb promptkövetés, ~2x lassabb
    "shift": 8.0,
    "sampler": "euler",
    "scheduler": "simple",
    "motion_latent": 1,
    "lightx2v_high": 0.5,          # SVI ajánlás: HIGH 0.5 (több mozgás), LOW 1.0
    "lightx2v_low": 1.0,
    "svi_ero": 1.0,
    "seed": None,                  # None = véletlen
    "modell_high": "Wan2.2-I2V-A14B-HighNoise-Q5_K_M.gguf",
    "modell_low": "Wan2.2-I2V-A14B-LowNoise-Q5_K_M.gguf",
    "szoveg_enkoder": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
    "vae": "wan_2.1_vae.safetensors",
    "svi_high": "SVI_v2_PRO_Wan2.2-I2V-A14B_HIGH_lora_rank_128_fp16.safetensors",
    "svi_low": "SVI_v2_PRO_Wan2.2-I2V-A14B_LOW_lora_rank_128_fp16.safetensors",
    "lx_high": "Wan_2_2_I2V_A14B_HIGH_lightx2v_4step_lora_260412_rank_64_fp16.safetensors",
    "lx_low": "Wan_2_2_I2V_A14B_LOW_lightx2v_4step_lora_260412_rank_64_fp16.safetensors",
}


def ffmpeg_utvonal():
    """Előbb a mappába tett ffmpeg\\ffmpeg.exe, utána a PATH."""
    helyi = ALAP / "ffmpeg" / "ffmpeg.exe"
    if helyi.is_file():
        return str(helyi)
    talalt = shutil.which("ffmpeg")
    if not talalt:
        raise SystemExit("Nem találom az ffmpeg-et. Telepítsd (winget install Gyan.FFmpeg), vagy tedd ide: ffmpeg\\ffmpeg.exe")
    return talalt


def meret(kep_utvonal, terulet):
    from PIL import Image
    w, h = Image.open(kep_utvonal).size
    arany = w / h
    H = (terulet / arany) ** 0.5
    W = H * arany
    return int(round(W / 16)) * 16, int(round(H / 16)) * 16


def graf(c, i, prompt, kep_nev, w, h, elozo_latens, seed, futas):
    """Egy klip ComfyUI API-gráfja."""
    g = {
        "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": c["modell_high"]}},
        "2": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": c["modell_low"]}},
        "3": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": c["svi_high"], "strength_model": c["svi_ero"]}},
        "4": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["3", 0], "lora_name": c["lx_high"], "strength_model": c["lightx2v_high"]}},
        "5": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["2", 0], "lora_name": c["svi_low"], "strength_model": c["svi_ero"]}},
        "6": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["5", 0], "lora_name": c["lx_low"], "strength_model": c["lightx2v_low"]}},
        "7": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["4", 0], "shift": c["shift"]}},
        "8": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["6", 0], "shift": c["shift"]}},
        "10": {"class_type": "CLIPLoader", "inputs": {"clip_name": c["szoveg_enkoder"], "type": "wan", "device": "default"}},
        "11": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["10", 0], "text": prompt}},
        "12": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["10", 0], "text": c["negativ"]}},
        "13": {"class_type": "VAELoader", "inputs": {"vae_name": c["vae"]}},
        "20": {"class_type": "LoadImage", "inputs": {"image": kep_nev}},
        "21": {"class_type": "ImageScale", "inputs": {"image": ["20", 0], "upscale_method": "lanczos", "width": w, "height": h, "crop": "center"}},
        "22": {"class_type": "VAEEncode", "inputs": {"pixels": ["21", 0], "vae": ["13", 0]}},
        "30": {"class_type": "WanImageToVideoSVIPro", "inputs": {
            "positive": ["11", 0], "negative": ["12", 0], "length": c["kocka_per_klip"],
            "anchor_samples": ["22", 0], "motion_latent_count": c["motion_latent"]}},
        "40": {"class_type": "KSamplerAdvanced", "inputs": {
            "model": ["7", 0], "add_noise": "enable", "noise_seed": seed, "steps": c["lepesek"], "cfg": c["cfg"],
            "sampler_name": c["sampler"], "scheduler": c["scheduler"], "positive": ["30", 0], "negative": ["30", 1],
            "latent_image": ["30", 2], "start_at_step": 0, "end_at_step": c["valtas_lepes"],
            "return_with_leftover_noise": "enable"}},
        "41": {"class_type": "KSamplerAdvanced", "inputs": {
            "model": ["8", 0], "add_noise": "disable", "noise_seed": seed, "steps": c["lepesek"], "cfg": c["cfg"],
            "sampler_name": c["sampler"], "scheduler": c["scheduler"], "positive": ["30", 0], "negative": ["30", 1],
            "latent_image": ["40", 0], "start_at_step": c["valtas_lepes"], "end_at_step": 10000,
            "return_with_leftover_noise": "disable"}},
        "50": {"class_type": "SaveLatent", "inputs": {"samples": ["41", 0], "filename_prefix": f"latents/svi_{futas}/klip{i:03d}"}},
        "51": {"class_type": "VAEDecode", "inputs": {"samples": ["41", 0], "vae": ["13", 0]}},
        "52": {"class_type": "SaveImage", "inputs": {"images": ["51", 0], "filename_prefix": f"svi_{futas}/klip{i:03d}/k"}},
    }
    if elozo_latens:
        g["31"] = {"class_type": "LoadLatent", "inputs": {"latent": elozo_latens}}
        g["30"]["inputs"]["prev_samples"] = ["31", 0]
    return g


def keres(ut, adat=None):
    req = urllib.request.Request(SERVER + ut, data=json.dumps(adat).encode() if adat is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def futtat(g):
    try:
        pid = keres("/prompt", {"prompt": g})["prompt_id"]
    except urllib.error.HTTPError as e:
        raise SystemExit("ComfyUI elutasította a feladatot:\n" + e.read().decode(errors="replace"))
    while True:
        time.sleep(3)
        h = keres(f"/history/{pid}")
        if pid in h:
            st = h[pid].get("status", {})
            if st.get("status_str") == "error":
                raise SystemExit("Hiba a generálás közben:\n" + json.dumps(st.get("messages", []), ensure_ascii=False, indent=1)[-3000:])
            if st.get("completed"):
                return h[pid]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    feladat = Path(sys.argv[1]).resolve()
    c = dict(ALAPERTELMEZES)
    c.update(json.loads(feladat.read_text(encoding="utf-8")))
    try:
        keres("/system_stats")
    except Exception:
        raise SystemExit("A ComfyUI nem fut. Indítsd el: ComfyUI_inditas.bat, és várd meg, míg betölt.")
    ffmpeg_utvonal()  # már az elején kiderüljön, ha hiányzik

    kep = Path(c["kep"])
    if not kep.is_absolute():
        kep = feladat.parent / kep
    futas = time.strftime("%Y%m%d_%H%M%S")
    kep_nev = f"svi_{futas}{kep.suffix}"
    shutil.copy(kep, COMFY / "input" / kep_nev)
    w, h = meret(kep, c["terulet"])

    promptok = c["promptok"]
    n = c["klipek_szama"] or len(promptok)
    seed = c["seed"] if c["seed"] is not None else random.randint(0, 2**31)
    print(f"{n} klip, {w}x{h}, ~{(n * (c['kocka_per_klip'] - 1) + 1) / c['fps']:.0f} mp, seed {seed}")

    elozo = None
    t0 = time.time()
    for i in range(n):
        p = promptok[min(i, len(promptok) - 1)]
        t = time.time()
        print(f"[{i + 1}/{n}] {p[:90]}")
        futtat(graf(c, i, p, kep_nev, w, h, elozo, seed + i * 123, futas))
        # az elkészült latenst átmásoljuk az input mappába, a következő klip innen tölti be
        lat_dir = COMFY / "output" / "latents" / f"svi_{futas}"
        legujabb = sorted(lat_dir.glob(f"klip{i:03d}*.latent"))[-1]
        elozo = f"svi_{futas}_klip{i:03d}.latent"
        shutil.copy(legujabb, COMFY / "input" / elozo)
        eltelt = time.time() - t
        print(f"      kész {eltelt:.0f} mp alatt, hátra kb. {eltelt * (n - i - 1) / 60:.0f} perc")

    # összefűzés: a 2. kliptől az első kocka (a horgonykép) kimarad
    kepek = []
    for i in range(n):
        kk = sorted((COMFY / "output" / f"svi_{futas}" / f"klip{i:03d}").glob("k_*.png"))
        kepek += kk if i == 0 else kk[1:]
    ki_dir = ALAP / "kimenet"
    ki_dir.mkdir(exist_ok=True)
    lista = ki_dir / f"_lista_{futas}.txt"
    lista.write_text("".join(f"file '{k.as_posix()}'\nduration {1 / c['fps']:.6f}\n" for k in kepek), encoding="utf-8")
    ki = ki_dir / f"{feladat.stem}_{futas}.mp4"
    subprocess.run([ffmpeg_utvonal(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-r", str(c["fps"]), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", str(ki)], check=True)
    lista.unlink()
    (ki_dir / f"{feladat.stem}_{futas}.json").write_text(json.dumps({**c, "seed": seed, "meret": [w, h]}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"KÉSZ: {ki}  ({len(kepek)} kocka, {len(kepek) / c['fps']:.1f} mp, {(time.time() - t0) / 60:.1f} perc)")


if __name__ == "__main__":
    main()
