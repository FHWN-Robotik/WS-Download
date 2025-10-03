import os
import sys
import shutil
import zipfile
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

TARGET_DIR = r"C:\Temp"  # Zielverzeichnis
REPOS = [
    "FHWN-Robotik/WS-KI",
    "FHWN-Robotik/WS-IndRob",
    "FHWN-Robotik/WS-MobRob",
]
# Optional: GitHub Token für private Repos / höhere Limits (oder setze env GH_TOKEN)
GITHUB_TOKEN = os.environ.get("GH_TOKEN", "").strip()

def log(msg): print(msg, flush=True)

def zip_url(owner_repo: str, branch: str) -> str:
    # codeload ist optimal für ZIP-Downloads
    return f"https://codeload.github.com/{owner_repo}/zip/refs/heads/{branch}"

def try_open(url: str):
    req = urllib.request.Request(url)
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
    return urllib.request.urlopen(req, timeout=120)

def download_zip(owner_repo: str, dest_zip: Path) -> None:
    # Versuche main -> master
    for branch in ("main", "master"):
        url = zip_url(owner_repo, branch)
        log(f"Lade {owner_repo} ({branch})...")
        try:
            with try_open(url) as resp, open(dest_zip, "wb") as f:
                shutil.copyfileobj(resp, f)
            log(f"OK: {owner_repo} ({branch})")
            return
        except urllib.error.HTTPError as e:
            if e.code == 404:
                log(f"Branch {branch} nicht gefunden, versuche nächsten…")
                continue
            raise
    raise RuntimeError(f"Konnte {owner_repo} weder auf main noch master laden.")

def extract_zip(zip_path: Path, extract_to: Path) -> Path:
    # GitHub-ZIP entpackt in einen Unterordner wie <repo>-<hash>; den ermitteln wir
    with zipfile.ZipFile(zip_path, "r") as zf:
        top_names = set(p.split("/")[0] for p in zf.namelist() if "/" in p)
        if not top_names:
            raise RuntimeError("ZIP scheint leer/ungewöhnlich zu sein.")
        root = list(top_names)[0]
        zf.extractall(extract_to)
        return extract_to / root

def replace_dir(src: Path, dst: Path):
    if dst.exists():
        # Lösche Ziel (robust gegen schreibgeschützte Dateien)
        def onerror(func, path, exc_info):
            try:
                os.chmod(path, 0o700); func(path)
            except Exception: pass
        shutil.rmtree(dst, onerror=onerror)
    shutil.move(str(src), str(dst))

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def main():
    # Optional: Zielverzeichnis per Argument überschreiben
    global TARGET_DIR
    if len(sys.argv) > 1:
        TARGET_DIR = sys.argv[1]
    target = Path(TARGET_DIR)
    ensure_dir(target)

    # Schreibtest
    try:
        with open(target / "_write_test.tmp", "w") as f: f.write("ok")
        (target / "_write_test.tmp").unlink(missing_ok=True)
    except Exception as e:
        raise SystemExit(f"Schreibtest fehlgeschlagen für {target}: {e}")

    with tempfile.TemporaryDirectory() as tmpd:
        tmp = Path(tmpd)
        for owner_repo in REPOS:
            repo_name = owner_repo.split("/")[-1]
            final_dst = target / repo_name

            zip_path = tmp / f"{repo_name}.zip"
            try:
                download_zip(owner_repo, zip_path)
            except Exception as e:
                log(f"FEHLER beim Laden {owner_repo}: {e}")
                continue

            try:
                unpack_root = extract_zip(zip_path, tmp)
            except Exception as e:
                log(f"FEHLER beim Entpacken {owner_repo}: {e}")
                continue

            try:
                replace_dir(unpack_root, final_dst)
            except Exception as e:
                log(f"FEHLER beim Ersetzen von {final_dst}: {e}")
                continue

            log(f"Bereit: {final_dst}")

    log("Fertig.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ABBRUCH: {e}")
        input("Taste drücken, um zu schließen…")
        sys.exit(1)
