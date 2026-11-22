"""
Videókészítő varázsló: megkérdezi a kezdőképet, a témát és a hosszt,
a helyi Ollama (gemma4) megírja a klipenkénti angol promptokat,
majd elindítja a hosszu_video.py-t. Ha a ComfyUI nem fut, elindítja.
"""
import base64, json, math, os, re, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

ALAP = Path(__file__).resolve().parent
PORTABLE = ALAP / "ComfyUI_windows_portable"
PYTHON = PORTABLE / "python_embeded" / "python.exe"
COMFY = "http://127.0.0.1:8188"
OLLAMA = "http://127.0.0.1:11434"
LLM = "gemma4:12b"
FPS, KOCKA = 16, 81

RENDSZER = """You write prompts for an image-to-video AI (Wan 2.2) that makes a long video from consecutive 5-second clips.
All clips start from the SAME starting image and continue each other seamlessly.
Rules:
- Write exactly {n} prompts in English, one per 5-second clip, in story order.
- Each prompt: 1-2 sentences describing what happens in those 5 seconds (action, motion, facial expression) plus camera movement.
- Keep the same main subject and location as the image; refer to the subject simply (e.g. "the girl", "the man", "the dog").
- Do NOT describe clothing, hair or colors in detail; the image already fixes the appearance.
- Actions must be physically simple and continue naturally from the previous clip; no scene cuts, no new locations unless the story requires a slow, continuous transition.
- No text, subtitles or logos.
Return JSON: {{"promptok": ["...", "..."]}}"""


def http(url, adat=None, timeout=30):
    req = urllib.request.Request(url, data=json.dumps(adat).encode() if adat is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read() or b"{}")


def fut(url):
    try:
        urllib.request.urlopen(url, timeout=3)
        return True
    except Exception:
        return False


def comfy_indit():
    if fut(COMFY + "/system_stats"):
        return None
    print("  (A ComfyUI nem fut, elindítom egy külön ablakban...)")
    return subprocess.Popen([str(ALAP / "ComfyUI_inditas.bat")], cwd=str(ALAP),
                            creationflags=subprocess.CREATE_NEW_CONSOLE)


def kerdez(szoveg, alap=None):
    s = input(f"{szoveg}{f' [{alap}]' if alap is not None else ''}: ").strip()
    return s if s else (alap if alap is not None else "")


def llm_valaszt():
    """gemma4:12b, ha megvan; különben egy másik telepített, képet is értő vagy általános modell."""
    try:
        nevek = [m["name"] for m in http(OLLAMA + "/api/tags", timeout=5).get("models", [])]
    except Exception:
        raise ValueError("az Ollama nem fut vagy nincs telepítve")
    if not nevek:
        raise ValueError("nincs letöltött Ollama-modell (javasolt: ollama pull gemma4:12b)")
    for kedvenc in (LLM, "gemma4", "gemma3:12b", "gemma3", "qwen2.5vl", "llava", "qwen3", "qwen2.5", "llama3.1"):
        for n in nevek:
            if n == kedvenc or n.startswith(kedvenc):
                return n
    return nevek[0]


def promptokat_ir(tema, n, kep):
    modell = llm_valaszt()
    print(f"   (modell: {modell})")
    try:
        http(COMFY + "/free", {"unload_models": True, "free_memory": True})  # VRAM felszabadítása az LLM-nek
    except Exception:
        pass
    uzenet = {"role": "user", "content": f"Story / topic (may be in Hungarian): {tema}\n\nWrite {n} clip prompts.",
              "images": [base64.b64encode(kep.read_bytes()).decode()]}
    body = {"model": modell, "stream": False, "keep_alive": 0,
            "format": {"type": "object", "properties": {"promptok": {"type": "array", "items": {"type": "string"}}},
                       "required": ["promptok"]},
            "messages": [{"role": "system", "content": RENDSZER.format(n=n)}, uzenet]}
    try:
        valasz = http(OLLAMA + "/api/chat", body, timeout=600)
    except urllib.error.HTTPError:
        # a modell nem kezel képet: próbáljuk kép nélkül
        uzenet.pop("images", None)
        valasz = http(OLLAMA + "/api/chat", body, timeout=600)
    p = json.loads(valasz["message"]["content"])["promptok"]
    p = [x.strip() for x in p if x.strip()]
    if not p:
        raise ValueError("üres válasz")
    return (p + [p[-1]] * n)[:n]


def kezi_promptok(n):
    print(f"Írj {n} angol promptot, klipenként egyet (üres sor = az előző ismétlése):")
    p = []
    for i in range(n):
        s = input(f"  {i + 1}. ").strip()
        p.append(s or (p[-1] if p else "The subject moves naturally, gentle camera movement."))
    return p


def mutat(promptok):
    print()
    for i, p in enumerate(promptok):
        print(f"  {i + 1:2d}. [{i * 5:3d}–{i * 5 + 5:3d} mp] {p}")
    print()


def main():
    os.system("")  # ANSI a Windows konzolon
    print("=" * 64)
    print("  HOSSZÚ VIDEÓ KÉSZÍTŐ  —  Wan 2.2 + Stable Video Infinity")
    print("=" * 64)
    comfy_folyamat = comfy_indit()

    # 1. kezdőkép
    while True:
        s = kerdez("\n1) Kezdőkép (húzd ide a képfájlt, majd Enter)").strip('"').strip("'").strip()
        kep = Path(s)
        if s and kep.is_file() and kep.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
            break
        print("   Nem találom ezt a képet, próbáld újra.")

    # 2. téma
    tema = ""
    while not tema:
        tema = kerdez("\n2) Mi történjen a videóban? (magyarul is lehet, pár mondat)")

    # 3. hossz
    while True:
        try:
            mp = int(kerdez("\n3) Milyen hosszú legyen? (másodperc)", "30"))
            if mp >= 5:
                break
        except ValueError:
            pass
        print("   Legalább 5 másodpercet adj meg, számmal.")
    n = max(1, math.ceil((mp * FPS - 1) / (KOCKA - 1)))

    # 4. minőség
    mod = kerdez("\n4) Gyors (g) vagy minőségi (m) mód? A minőségi pontosabban követi a szöveget, de kétszer lassabb", "g").lower()
    cfg = 1.5 if mod.startswith("m") else 1.0
    perc = n * (148 if cfg == 1.0 else 280) / 60
    print(f"\n   → {n} klip, kb. {(n * (KOCKA - 1) + 1) / FPS:.0f} mp videó, becsült idő: kb. {perc:.0f} perc")

    # 5. promptok
    promptok = None
    while promptok is None:
        print("\n5) A promptokat a helyi AI (Ollama) írja meg a témából... (fél-egy perc)")
        try:
            promptok = promptokat_ir(tema, n, kep)
        except Exception as e:
            print(f"   Nem sikerült ({e}).")
            if kerdez("   Megírod kézzel? (i/n)", "i").lower().startswith("i"):
                promptok = kezi_promptok(n)
            else:
                continue
        while True:
            mutat(promptok)
            v = kerdez("Enter = indítás,  u = új promptok,  sz = egy sor átírása,  k = kilépés", "").lower()
            if v == "":
                break
            if v == "k":
                sys.exit(0)
            if v == "u":
                promptok = None
                break
            if v.startswith("sz"):
                try:
                    i = int(kerdez("   Hányadik sort írod át?")) - 1
                    promptok[i] = kerdez("   Új szöveg (angolul)", promptok[i])
                except (ValueError, IndexError):
                    print("   Érvénytelen sorszám.")

    # 6. feladat mentése és indítás
    nev = kerdez("\n6) A videó neve (fájlnév)", re.sub(r"[^\w]+", "_", tema.lower())[:30].strip("_") or "video")
    nev = re.sub(r'[<>:"/\\|?*]+', "_", nev)
    fdir = ALAP / "feladatok"
    fdir.mkdir(exist_ok=True)
    feladat = fdir / f"{nev}.json"
    feladat.write_text(json.dumps({"kep": str(kep.resolve()), "tema": tema, "promptok": promptok,
                                   "klipek_szama": n, "cfg": cfg}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   Feladat elmentve: {feladat}  (később újra futtatható: húzd a Hosszu_video.bat-ra)")

    print("\nVárakozás a ComfyUI-ra...", end="", flush=True)
    for _ in range(300):
        if fut(COMFY + "/system_stats"):
            break
        time.sleep(2)
        print(".", end="", flush=True)
    else:
        sys.exit("\nA ComfyUI nem indult el. Nézd meg a ComfyUI ablakát.")
    print(" kész.\n", flush=True)

    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    r = subprocess.run([str(PYTHON), "-s", str(ALAP / "hosszu_video.py"), str(feladat)], env=env)
    if r.returncode == 0:
        ki = sorted((ALAP / "kimenet").glob(f"{nev}_*.mp4"), key=lambda p: p.stat().st_mtime)
        if ki:
            print(f"\nA videó: {ki[-1]}")
            os.startfile(ki[-1])
    else:
        print("\nHiba történt, lásd fent.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nMegszakítva.")
