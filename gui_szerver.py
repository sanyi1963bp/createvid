"""
Grafikus felület a hosszú videó készítéshez: helyi webszerver (csak a saját gépről érhető el),
a felület a böngészőben nyílik meg: http://127.0.0.1:8190
Nem kell hozzá semmit telepíteni, a ComfyUI beágyazott Pythonjával fut.
"""
import json, math, mimetypes, os, re, sys, threading, time, traceback, urllib.parse, urllib.request, webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

ALAP = Path(__file__).resolve().parent
sys.path.insert(0, str(ALAP))
import hosszu_video as hv      # noqa: E402
import video_keszito as vk     # noqa: E402

PORT = 8190
GUI = ALAP / "gui" / "index.html"
KEPEK = ALAP / "kepek"
FELADATOK = ALAP / "feladatok"
KIMENET = ALAP / "kimenet"
FPS, KOCKA = 16, 81
ENGEDETT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".mp4"}

zar = threading.Lock()
allapot = {"fut": False, "fazis": "tetlen", "n": 0, "kesz": 0, "hatra": None, "log": [],
           "video": None, "hiba": None, "elonezet": None, "nev": None, "kezdes": None}
leallit = threading.Event()


def frissit(**k):
    with zar:
        allapot.update(k)


def naplo(szoveg):
    with zar:
        allapot["log"] = (allapot["log"] + [time.strftime("%H:%M:%S ") + szoveg])[-200:]


def comfy_dolgozik():
    """Fut-e éppen (vagy vár-e) feladat a ComfyUI-ban, bárhonnan indították."""
    try:
        with urllib.request.urlopen(vk.COMFY + "/queue", timeout=3) as r:
            q = json.loads(r.read())
        return bool(q.get("queue_running") or q.get("queue_pending"))
    except Exception:
        return False


def klipszam(mp):
    return max(1, math.ceil((mp * FPS - 1) / (KOCKA - 1)))


def biztonsagos_nev(s, alap="video"):
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", s).strip(" ._")
    return s[:60] or alap


# ------------------------------------------------------------------ generálás háttérszálon
def munka(c, nev):
    leallit.clear()
    frissit(fut=True, fazis="indul", n=c.get("klipek_szama") or len(c["promptok"]), kesz=0, hatra=None,
            log=[], video=None, hiba=None, elonezet=None, nev=nev, kezdes=time.time())
    try:
        if not vk.fut(vk.COMFY + "/system_stats"):
            naplo("A ComfyUI nem fut, elindítom (külön ablakban)...")
            frissit(fazis="comfy")
            vk.comfy_indit()
            for _ in range(300):
                if vk.fut(vk.COMFY + "/system_stats") or leallit.is_set():
                    break
                time.sleep(2)
            if not vk.fut(vk.COMFY + "/system_stats"):
                raise RuntimeError("A ComfyUI nem indult el. Nézd meg a ComfyUI ablakát.")
            naplo("A ComfyUI fut.")

        def jelent(szoveg, tipus=None, **a):
            naplo(szoveg.strip())
            if tipus == "start":
                frissit(fazis="general", n=a["n"])
            elif tipus == "klip":
                frissit(fazis="general", aktualis=a["i"] + 1)
            elif tipus == "klip_kesz":
                frissit(kesz=a["i"] + 1, hatra=a["hatra"], elonezet=a.get("elonezet"))
            elif tipus == "osszefuzes":
                frissit(fazis="osszefuzes")
            elif tipus == "kesz":
                frissit(video=a["video"])

        ki = hv.generalas(c, nev, ALAP, jelent=jelent, megallit=leallit.is_set)
        frissit(fazis="kesz", video=str(ki))
    except hv.Megallitva as e:
        naplo(str(e))
        frissit(fazis="leallitva")
    except BaseException as e:  # a hosszu_video SystemExit-tel is jelezhet hibát
        szoveg = str(e) or e.__class__.__name__
        if leallit.is_set():
            naplo("Leállítva.")
            frissit(fazis="leallitva")
        else:
            naplo("HIBA: " + szoveg)
            traceback.print_exc()
            frissit(fazis="hiba", hiba=szoveg)
    finally:
        frissit(fut=False)


# ------------------------------------------------------------------ HTTP
class Kezelo(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def valasz(self, adat, kod=200):
        b = json.dumps(adat, ensure_ascii=False).encode()
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def torzs(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def fajl_kuld(self, ut, tipus=None):
        ut = Path(ut)
        if not ut.is_file():
            return self.send_error(404)
        meret = ut.stat().st_size
        tipus = tipus or mimetypes.guess_type(ut.name)[0] or "application/octet-stream"
        tart = self.headers.get("Range")
        eleje, vege = 0, meret - 1
        if tart and tart.startswith("bytes="):
            a, _, b = tart[6:].partition("-")
            eleje = int(a) if a else max(0, meret - int(b))
            vege = int(b) if a and b else meret - 1
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {eleje}-{vege}/{meret}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", tipus)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(vege - eleje + 1))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        try:
            with open(ut, "rb") as f:
                f.seek(eleje)
                maradt = vege - eleje + 1
                while maradt > 0:
                    d = f.read(min(1 << 20, maradt))
                    if not d:
                        break
                    self.wfile.write(d)
                    maradt -= len(d)
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            pass

    # ---------------- GET
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = dict(urllib.parse.parse_qsl(u.query))
        if u.path in ("/", "/index.html"):
            return self.fajl_kuld(GUI, "text/html; charset=utf-8")
        if u.path == "/fajl":
            ut = Path(q.get("ut", ""))
            if ut.suffix.lower() not in ENGEDETT:
                return self.send_error(403)
            return self.fajl_kuld(ut)
        if u.path == "/api/allapot":
            with zar:
                a = dict(allapot)
            return self.valasz(a)
        if u.path == "/api/rendszer":
            ollama = vk.fut(vk.OLLAMA + "/api/tags")
            return self.valasz({"comfy": vk.fut(vk.COMFY + "/system_stats"), "ollama": ollama,
                                "alap": {k: hv.ALAPERTELMEZES[k] for k in
                                         ("cfg", "terulet", "lightx2v_high", "lightx2v_low", "fps", "kocka_per_klip")}})
        if u.path == "/api/feladatok":
            lista = []
            for p in sorted(FELADATOK.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
                try:
                    d = json.loads(p.read_text(encoding="utf-8"))
                    lista.append({"nev": p.stem, "n": d.get("klipek_szama") or len(d.get("promptok", [])), "adat": d})
                except Exception:
                    pass
            return self.valasz(lista)
        if u.path == "/api/kimenetek":
            lista = [{"nev": p.stem, "ut": str(p), "meret_mb": round(p.stat().st_size / 1e6, 1),
                      "ido": time.strftime("%Y-%m-%d %H:%M", time.localtime(p.stat().st_mtime))}
                     for p in sorted(KIMENET.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)]
            return self.valasz(lista)
        self.send_error(404)

    # ---------------- POST
    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        try:
            if u.path == "/api/kep":
                nev = biztonsagos_nev(urllib.parse.unquote(self.headers.get("X-Fajlnev", "kep.png")), "kep.png")
                if Path(nev).suffix.lower() not in ENGEDETT - {".mp4"}:
                    return self.valasz({"hiba": "Csak kép tölthető fel (png, jpg, webp, bmp)."}, 400)
                adat = self.torzs()
                KEPEK.mkdir(exist_ok=True)
                cel = KEPEK / nev
                i = 1
                while cel.exists() and cel.stat().st_size != len(adat):
                    cel = KEPEK / f"{Path(nev).stem}_{i}{Path(nev).suffix}"
                    i += 1
                cel.write_bytes(adat)
                from PIL import Image
                w, h = Image.open(cel).size
                return self.valasz({"ut": str(cel), "w": w, "h": h})

            d = json.loads(self.torzs() or b"{}")
            if u.path == "/api/promptok":
                kep = Path(d["kep"])
                n = int(d["n"])
                if allapot["fut"] or comfy_dolgozik():
                    return self.valasz({"hiba": "A ComfyUI most generál; a promptíró AI csak utána használható "
                                                "(a videómemória kell neki). Addig kézzel is beírhatod a promptokat."}, 409)
                p = vk.promptokat_ir(d["tema"], n, kep)
                return self.valasz({"promptok": p})

            if u.path == "/api/inditas":
                if allapot["fut"]:
                    return self.valasz({"hiba": "Már fut egy generálás."}, 409)
                if comfy_dolgozik():
                    return self.valasz({"hiba": "A ComfyUI épp egy másik generáláson dolgozik (pl. a Hosszu_video.bat-ból). "
                                                "Várd meg, amíg végez."}, 409)
                promptok = [p.strip() for p in d.get("promptok", []) if p.strip()]
                if not promptok:
                    return self.valasz({"hiba": "Nincs egy prompt sem."}, 400)
                if not Path(d.get("kep", "")).is_file():
                    return self.valasz({"hiba": "Nincs kezdőkép kiválasztva."}, 400)
                nev = biztonsagos_nev(d.get("nev") or "video")
                c = {"kep": d["kep"], "tema": d.get("tema", ""), "promptok": promptok,
                     "klipek_szama": len(promptok), "cfg": float(d.get("cfg", 1.0))}
                for k in ("terulet", "lightx2v_high", "lightx2v_low"):
                    if d.get(k) not in (None, ""):
                        c[k] = type(hv.ALAPERTELMEZES[k])(d[k])
                if str(d.get("seed", "")).strip():
                    c["seed"] = int(d["seed"])
                if d.get("negativ_extra", "").strip():
                    c["negativ"] = hv.ALAPERTELMEZES["negativ"] + ", " + d["negativ_extra"].strip()
                FELADATOK.mkdir(exist_ok=True)
                (FELADATOK / f"{nev}.json").write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
                threading.Thread(target=munka, args=(c, nev), daemon=True).start()
                return self.valasz({"ok": True, "nev": nev})

            if u.path == "/api/leallitas":
                leallit.set()
                naplo("Leállítás kérve: az épp készülő klip megszakad...")
                try:
                    urllib.request.urlopen(urllib.request.Request(vk.COMFY + "/interrupt", data=b"{}",
                                                                  headers={"Content-Type": "application/json"}), timeout=5)
                except Exception:
                    pass
                return self.valasz({"ok": True})

            if u.path == "/api/megnyit":
                ut = Path(d.get("ut", ""))
                if ut.suffix.lower() == ".mp4" and ut.is_file():
                    os.startfile(ut)
                elif d.get("mappa"):
                    os.startfile(KIMENET)
                return self.valasz({"ok": True})
        except Exception as e:
            traceback.print_exc()
            return self.valasz({"hiba": str(e)}, 500)
        self.send_error(404)


def main():
    os.system("")
    cim = f"http://127.0.0.1:{PORT}"
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), Kezelo)
    except OSError:
        print(f"A felület már fut, megnyitom: {cim}")
        webbrowser.open(cim)
        return
    print("=" * 60)
    print("  HOSSZÚ VIDEÓ KÉSZÍTŐ – grafikus felület")
    print(f"  Böngészőben: {cim}")
    print("  Ezt az ablakot hagyd nyitva, amíg használod (bezárás = kilépés).")
    print("=" * 60)
    threading.Timer(1.0, lambda: webbrowser.open(cim)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
