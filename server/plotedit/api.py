#!/usr/bin/env python3
"""The read-only half of the service: what the fixtures are, what the gels are,
and what a given rig would actually do.

    cd server && uvicorn plotedit.api:app --reload
    curl localhost:8000/fixtures

Nothing here writes a file or changes state. Export and editing come later.

⚠ Every photometric and gel figure carries its source, and the API passes those
sources through rather than stripping them. A number without provenance is how
the EDLT figures got mistaken for standard-tube figures in the first place.
"""
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import photometrics as ph

app = FastAPI(
    title="plotedit",
    description="Light plot computation. Read-only.",
    version="0.1.0",
)

# The front end is served from a dev server on another port during development.
# Localhost only — this is a tool that runs on the designer's laptop at tech,
# not a service on a network.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------- models

class Instrument(BaseModel):
    """One unit on the plot. Field names follow the Vectorworks/Lightwright
    exchange, so paperwork.py imports old shows with no translation."""
    unit: Optional[int] = None
    channel: Optional[int] = None
    type: str = Field(..., description='A key in FIXTURES, e.g. "S4 26"')
    x: float = Field(..., description="Feet, stage coordinates")
    y: float = Field(..., description="Feet")
    trim: Optional[float] = Field(None, description="Hang height in feet")
    focus_x: Optional[float] = None
    focus_y: Optional[float] = None
    focus_h: float = Field(5.5, description="Head height at the focus point, feet")
    color: Optional[str] = Field(None, description='"R52+R119" stacks, "R52/R119" splits')
    lamp: Optional[str] = Field(None, description='e.g. "HPL 575" for a tungsten rig')
    mode: Optional[str] = Field(None, description='LED output mode, e.g. "Regulated 3200K"')
    position: Optional[str] = None
    purpose: Optional[str] = None


class ComputeRequest(BaseModel):
    instruments: List[Instrument]


class WashRequest(BaseModel):
    type: str
    throw: float
    width: Optional[float] = Field(None, description="Feet of acting area to cover")
    rule: str = Field("field-to-beam",
                      description="field-to-beam | beam-to-beam | field-to-field")


# ----------------------------------------------------------------- endpoints

@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "fixtures": len(ph.FIXTURES), "gels": len(ph.GELS)}


@app.get("/fixtures")
def fixtures() -> Dict[str, Any]:
    """Every fixture with its beam and field angles, candela, and its SOURCE.

    Keys say which lens tube: "Lustr 26 EDLT" is not the same fixture as a Lustr
    on a standard tube, and ETC publishes no figures for the latter.
    """
    out = {}
    for k, f in ph.FIXTURES.items():
        penumbra = (f["field"] - f["beam"]) if f["field"] and f["beam"] else None
        out[k] = {
            "field": f["field"],
            "beam": f["beam"],
            "penumbra_deg": round(penumbra, 1) if penumbra else None,
            "candela": f["cd"],
            "reference_lamp": f["ref_lamp"],
            "family": f["family"],
            "modes": list(f.get("modes", {})) or None,
            "source": f["source"],
        }
    return {"count": len(out), "fixtures": out}


@app.get("/gels")
def gels() -> Dict[str, Any]:
    """Gel transmissions, each with its source.

    Rosco publishes transmission for color filters on the website but NOT for
    the diffusions — those figures come from the myColor swatch app.
    """
    return {
        "count": len(ph.GELS),
        "notation": {
            "+": "stacked in one frame — transmissions multiply",
            "/": "a split frame, two gels cut diagonally — they do NOT multiply",
        },
        "gels": {k: {"name": v["name"], "transmission": v["t"], "source": v["source"]}
                 for k, v in ph.GELS.items()},
    }


@app.post("/compute")
def compute(req: ComputeRequest) -> Dict[str, Any]:
    """Throw, elevation, pan, pools and footcandles for each instrument.

    An instrument with no trim or no focus point gets `computed: false` and an
    explanation rather than a guessed number.
    """
    results = []
    for i, inst in enumerate(req.instruments):
        row: Dict[str, Any] = {"index": i, "unit": inst.unit, "channel": inst.channel,
                               "type": inst.type, "computed": False}
        if inst.type not in ph.FIXTURES:
            row["note"] = f"{inst.type} is not in the fixture table"
            results.append(row); continue
        if inst.trim is None or inst.focus_x is None or inst.focus_y is None:
            row["note"] = "needs a trim height and a focus point"
            results.append(row); continue

        a = ph.aim((inst.x, inst.y, inst.trim),
                   (inst.focus_x, inst.focus_y, inst.focus_h))
        row.update(computed=True,
                   throw=round(a["throw"], 2), throw_ft=ph.fmt_ft(a["throw"]),
                   elevation=round(a["elevation"], 1), pan=round(a["pan"], 1))

        pool = ph.pool(inst.type, a["throw"], a["elevation"])
        if pool.get("field"):
            row["field"] = round(pool["field"], 2)
            row["field_ft"] = ph.fmt_ft(pool["field"])
        if pool.get("beam"):
            row["beam"] = round(pool["beam"], 2)
            row["beam_ft"] = ph.fmt_ft(pool["beam"])
        if pool.get("on_deck_length"):
            row["on_deck_ft"] = ph.fmt_ft(pool["on_deck_length"])

        gel_arg = inst.color or None
        if gel_arg:
            factor, gnote = ph.gel_factor(gel_arg)
            row["gel_note"] = gnote
            if factor is None:
                gel_arg = None
                row["gel_warning"] = "no transmission figure; level is for open white"
        fc, note = ph.footcandles(inst.type, a["throw"], inst.lamp, inst.mode, gel_arg)
        row["footcandles"] = round(fc) if fc else None
        row["footcandles_note"] = note
        results.append(row)

    return {"count": len(results), "instruments": results}


@app.post("/wash")
def wash(req: WashRequest) -> Dict[str, Any]:
    """Spacing for a wash, and how many units cover a given width.

    Default rule is field-to-beam: each unit's field edge lands on the next
    unit's beam edge, so the overlap sits between the two beams.
    """
    try:
        w = ph.wash_spacing(req.type, req.throw, req.rule)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    out = {"type": req.type, "throw": req.throw, "rule": req.rule,
           "spacing": round(w["spacing"], 2), "spacing_ft": ph.fmt_ft(w["spacing"]),
           "field_radius_ft": ph.fmt_ft(w["field_r"]),
           "beam_radius_ft": ph.fmt_ft(w["beam_r"]),
           "penumbra_ft": ph.fmt_ft(w["penumbra"])}
    if req.width:
        r = ph.wash_row(req.type, req.throw, req.width, req.rule)
        out["row"] = {"count": r["count"], "spacing_ft": ph.fmt_ft(r["spacing"]),
                      "ideal_ft": ph.fmt_ft(r["ideal"]),
                      "positions": [round(p, 2) for p in r["positions"]]}
    return out


@app.get("/lens")
def lens(pool: float, throw: float, family: str = "S4") -> Dict[str, Any]:
    """Which barrel gives a pool of this size at this throw."""
    rows = ph.lens_for(pool, throw, family)
    if not rows:
        raise HTTPException(status_code=400, detail=f"no fixtures in family {family!r}")
    return {"wanted_ft": pool, "throw": throw, "family": family,
            "options": [{"type": k, "field_ft": ph.fmt_ft(d), "error_ft": round(e, 2)}
                        for k, d, e in rows]}
