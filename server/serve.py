#!/usr/bin/env python3
"""Run plotedit as ONE program: the API and the editor on one port.

⭐ Jerry, 2026.09.24: "it would be nice to set it up so that users that aren't
familiar with it at all could download it and run it."

In development the editor is a Vite dev server on :5173 that proxies /api to
this service on :8000 — two runtimes, two processes, two ports. That is fine for
someone changing the code and impossible for someone who just wants to draw a
plot: it means installing Node, installing Python, and knowing which terminal
does what.

⚠ THE API IS MOUNTED, NOT REWRITTEN. The existing app keeps all its routes at
the root, so every test that calls client.post("/compute") still does, and it is
mounted here under /api — which is the path the built front end already asks
for, because that is what Vite proxies in development. One arrangement, two ways
in, nothing to keep in step.

    python3 serve.py            # builds nothing; serves web/dist if it is there
"""
import os
import sys
import threading
import webbrowser
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from plotedit.api import app as api

HERE = Path(__file__).resolve().parent
DIST = HERE.parent / "web" / "dist"

root = FastAPI(title="plotedit", description="Light plot editor.")
root.mount("/api", api)


@root.get("/health")
def health():
    """Alive, and whether there is an editor to serve."""
    return {"ok": True, "editor": DIST.is_dir()}


def _mount_editor() -> bool:
    """Serve the built editor at /, if it has been built.

    ⚠ Says so rather than 404ing. "Not found" on the front page of a tool you
    just downloaded is indistinguishable from a broken download; the page below
    names the one command that fixes it.
    """
    if DIST.is_dir() and (DIST / "index.html").is_file():
        root.mount("/", StaticFiles(directory=str(DIST), html=True), name="editor")
        return True

    @root.get("/")
    def no_editor():
        return JSONResponse(status_code=503, content={
            "error": "The editor has not been built.",
            "fix": "cd web && npm install && npm run build",
            "note": "A release download has this already built — if you are "
                    "looking at this from a release, please report it.",
        })
    return False


def main(port: int = 8000, open_browser: bool = True) -> None:
    import uvicorn
    built = _mount_editor()
    url = f"http://127.0.0.1:{port}/"
    if not built:
        print("⚠ web/dist is missing — serving the API only.", file=sys.stderr)
        print("  Build the editor with:  cd web && npm install && npm run build",
              file=sys.stderr)
    print(f"plotedit → {url}   (ctrl-C to stop)")
    if open_browser:
        # ⚠ After a beat, and in a thread. Opening the browser before uvicorn is
        # listening gives the reader a connection error as their first
        # impression of the tool.
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    # ⚠ 127.0.0.1, never 0.0.0.0. This is a tool on a designer's laptop at
    # tech, and it can write files — it has no business being reachable from
    # the theatre's wifi.
    uvicorn.run(root, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main(port=int(os.environ.get("PLOTEDIT_PORT", "8000")),
         open_browser=os.environ.get("PLOTEDIT_NO_BROWSER") != "1")
