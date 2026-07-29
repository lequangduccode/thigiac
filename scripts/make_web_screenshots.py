"""Chup anh man hinh giao dien web (app.py) bang Playwright + Chrome he thong.

Trich 2 anh bo that tu zip LocBeef, khoi dong Flask, dieu khien trinh duyet
tai anh -> phan tich -> chup ket qua. Xuat PNG vao outputs/report_figures/.

Usage:
    python scripts/make_web_screenshots.py --zip "C:/Users/Admin/Downloads/archive (1).zip"
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
OUT = BASE_DIR / "outputs" / "report_figures"
TMP = BASE_DIR / "outputs" / "_web_tmp"
PORT = 5099


def extract_samples(zip_path: Path) -> tuple[Path, Path]:
    TMP.mkdir(parents=True, exist_ok=True)
    z = zipfile.ZipFile(zip_path)
    def first(cls: str) -> str:
        return sorted(
            n for n in z.namelist()
            if n.lower().endswith(".jpg") and "/test/" in n.lower() and f"/{cls}/" in n.lower()
        )[0]
    fresh_name, rotten_name = first("fresh"), first("rotten")
    fresh_p = TMP / "sample_fresh.jpg"
    rotten_p = TMP / "sample_spoiled.jpg"
    fresh_p.write_bytes(z.read(fresh_name))
    rotten_p.write_bytes(z.read(rotten_name))
    return fresh_p, rotten_p


def wait_health(url: str, timeout: float = 30.0) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return
        except Exception:  # noqa: BLE001
            time.sleep(0.5)
    raise RuntimeError("Server khong khoi dong kip")


def analyze_and_shot(page, container, img_path: Path, out_name: str) -> None:
    page.set_input_files("#file", str(img_path))
    page.wait_for_selector("#preview", state="visible")
    page.wait_for_timeout(400)
    page.click("#analyze")
    page.wait_for_selector(".badge", timeout=15000)
    page.wait_for_timeout(600)
    container.screenshot(path=str(OUT / out_name))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    fresh_p, spoiled_p = extract_samples(Path(args.zip))

    env = dict(os.environ, PORT=str(PORT))
    server = subprocess.Popen(
        [sys.executable, "-c",
         f"import os; os.environ['PORT']='{PORT}';"
         "import app; app.app.run(host='127.0.0.1', port=" + str(PORT) + ", use_reloader=False)"],
        cwd=str(BASE_DIR), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        wait_health(f"http://127.0.0.1:{PORT}/health")
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            page = browser.new_page(viewport={"width": 860, "height": 1000},
                                    device_scale_factor=2)
            page.goto(f"http://127.0.0.1:{PORT}/")
            page.wait_for_selector(".container")
            container = page.locator(".container")

            # 1. Trang tai anh (trang thai ban dau)
            page.wait_for_timeout(300)
            container.screenshot(path=str(OUT / "web_upload.png"))
            print("web_upload.png")

            # 2. Ket qua anh tuoi
            analyze_and_shot(page, container, fresh_p, "web_result_fresh.png")
            print("web_result_fresh.png")

            # 3. Ket qua anh hong (tai lai trang cho sach)
            page.reload()
            page.wait_for_selector(".container")
            container = page.locator(".container")
            analyze_and_shot(page, container, spoiled_p, "web_result_spoiled.png")
            print("web_result_spoiled.png")

            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except Exception:  # noqa: BLE001
            server.kill()
    print("Done ->", OUT)


if __name__ == "__main__":
    main()
