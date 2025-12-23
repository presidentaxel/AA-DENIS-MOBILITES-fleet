"""
Script d'enregistrement complet d'une session Heetch dans Chromium (Playwright).
Ce qu'il enregistre :
- Trace Playwright (captures, DOM snapshots, sources) : trace.zip
- HAR réseau (requêtes/réponses, corps embarqués) : network.har
- Console navigateur : console.log
- Cookies de tous les domaines : cookies.json
- Storages (localStorage + sessionStorage) de la page active : storage.json

Usage (dans le repo, depuis la racine) :
    python -m pip install playwright
    python -m playwright install chromium
    python backend/scripts/record_heetch_session.py
Ensuite : une fenêtre Chromium s'ouvre, fais tout le parcours manuellement.
Quand tu as terminé (arrivé sur le dashboard connecté), reviens au terminal et appuie sur Entrée.
Les artefacts sont écrits dans backend/scripts/heetch_artifacts/.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List

from playwright.async_api import async_playwright, ConsoleMessage


AUTH_URL = (
    "https://auth.heetch.com/?client_id=driver-portal"
    "&redirect_uri=https://driver.heetch.com/api/callback?requestURL=/dashboard"
)

ARTIFACTS_DIR = Path(__file__).parent / "heetch_artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


async def record_session():
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    trace_path = ARTIFACTS_DIR / f"trace-{timestamp}.zip"
    har_path = ARTIFACTS_DIR / f"network-{timestamp}.har"
    cookies_path = ARTIFACTS_DIR / f"cookies-{timestamp}.json"
    storage_path = ARTIFACTS_DIR / f"storage-{timestamp}.json"
    console_path = ARTIFACTS_DIR / f"console-{timestamp}.log"

    console_buffer: List[str] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Headful pour voir ce qui se passe
            slow_mo=200,     # Ralentir un peu les actions manuelles
        )

        context = await browser.new_context(
            record_har_path=str(har_path),
            record_har_content="embed",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/143.0.0.0 Safari/537.36",
        )

        page = await context.new_page()

        def on_console(msg: ConsoleMessage):
            line = f"[{msg.type.upper()}] {msg.text}"
            console_buffer.append(line)

        page.on("console", on_console)

        await context.tracing.start(
            name="heetch-session",
            title="Heetch session recording",
            screenshots=True,
            snapshots=True,
            sources=True,
        )

        print(f"[INFO] Chromium lancé. Navigation vers {AUTH_URL}")
        await page.goto(AUTH_URL, wait_until="load", timeout=90_000)
        print(
            "[ACTION] Fais le flux complet dans la fenêtre ouverte "
            "(login, éventuel SMS, mot de passe, dashboard)."
        )
        print("[ACTION] Quand tu as terminé et que la session est stable, appuie sur Entrée ici.")
        await asyncio.to_thread(input)  # Attend l'Entrée dans le terminal

        # Capture cookies
        cookies = await context.cookies()
        with cookies_path.open("w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        print(f"[OK] Cookies sauvegardés -> {cookies_path}")

        # Capture storages (localStorage + sessionStorage) de la page active
        storage = await page.evaluate(
            """() => ({
                localStorage: { ...localStorage },
                sessionStorage: { ...sessionStorage },
            })"""
        )
        with storage_path.open("w", encoding="utf-8") as f:
            json.dump(storage, f, indent=2, ensure_ascii=False)
        print(f"[OK] Storage sauvegardé -> {storage_path}")

        # Sauvegarde console
        if console_buffer:
            console_path.write_text("\n".join(console_buffer), encoding="utf-8")
            print(f"[OK] Console sauvegardée -> {console_path}")
        else:
            print("[OK] Aucune entrée console capturée.")

        # Stop trace
        await context.tracing.stop(path=str(trace_path))
        print(f"[OK] Trace Playwright -> {trace_path}")
        print(f"[OK] HAR réseau -> {har_path}")

        await context.close()
        await browser.close()

    print("\n=== Artefacts ===")
    print(f"- Trace       : {trace_path}")
    print(f"- HAR         : {har_path}")
    print(f"- Cookies     : {cookies_path}")
    print(f"- Storage     : {storage_path}")
    print(f"- Console log : {console_path if console_buffer else 'aucun'}")


if __name__ == "__main__":
    asyncio.run(record_session())

