"""What colour a gel makes the light, as sRGB, from the published chromaticity.

#148: `gels.csv` carries transmission — how MUCH light gets through — and nothing
about what colour it becomes. The show model therefore carried its own hand-written
map of seven hex values, and thirteen units rendered as warm white because their
filters were simply absent from it. ⚠ An unknown gel fell back to warm white rather
than failing, so nobody could see it.

#159 then published `gel_colour.csv`: CIE chromaticity for 609 of the 646 filters,
read from the makers' own technical data sheets, every row carrying its source URL
and the date it was read. ⭐ That cleared #148's real bar — *"no colour column
without a source column that can carry its weight."*

🔴 THIS FILE IS THE HALF THAT WAS STILL MISSING. Nothing read that CSV. The data
sat in the repo unused and `/api/gels` still answered with name, transmission and
source, so every consumer was still inventing its own colour.

⚠ A SINGLE RGB IS A SIMPLIFICATION HOWEVER IT IS DERIVED, and #148 says so. A gel
looks different under tungsten and under a white LED, and different again on skin
than on a cyc. Overlapping beams wash toward white in any additive renderer. This
module returns the best-sourced single value available and reports exactly which
illuminant it came from; it does not pretend that value is the whole truth.
"""

import csv
import os
from typing import Any, Dict, Optional

from .photometrics import gel_key

# ⭐ NEAREST-TO-TUNGSTEN FIRST, and this order is FORCED BY THE DATA rather than
# chosen. The three makers publish under different illuminants and NO ILLUMINANT
# IS COMMON TO ALL THREE:
#
#     GamColor   A only                  116 filters
#     LEE        C and TUNG3200          259 filters
#     Rosco      A and D65               234 filters
#
# So there is no single illuminant to standardise on — the best any choice can
# cover alone is 54%. This order covers all 609 and lands GamColor and Rosco on
# 2856K and LEE on 3200K, which are both tungsten and close to each other.
# ⚠ Every answer REPORTS the illuminant it used. Mixing a daylight figure into a
# plot of tungsten ones without saying so is the failure to avoid here.
ILLUMINANT_PREFERENCE = ("A", "TUNG3200", "C", "D65")

# CIE 1931 2° white points. A, C and D65 are the standard published values.
_WHITE_XY = {
    "A": (0.44757, 0.40745),
    "C": (0.31006, 0.31616),
    "D65": (0.31272, 0.32903),
}

# sRGB's own white point, which is where everything has to end up.
_D65 = _WHITE_XY["D65"]


def _planckian_xy(temp_k: float) -> tuple:
    """The chromaticity of a blackbody at `temp_k`, 1667K–4000K.

    Kim et al.'s cubic approximation of the Planckian locus — the usual closed
    form, good to about 5e-5 in xy over this range.

    ⭐ COMPUTED RATHER THAN TYPED IN. A hardcoded (0.4234, 0.3990) for 3200K is a
    number nobody downstream can check; a formula with a name can be re-derived,
    and the test pins it against the published value.
    """
    t = float(temp_k)
    x = (-0.2661239e9 / t**3) - (0.2343589e6 / t**2) + (0.8776956e3 / t) + 0.179910
    y = (-0.9549476 * x**3) - (1.37418593 * x**2) + (2.09137015 * x) - 0.16748867
    return (x, y)


# LEE's second figure is published against a 3200K tungsten source rather than a
# CIE standard illuminant, so its white point comes off the Planckian locus.
_WHITE_XY["TUNG3200"] = _planckian_xy(3200)

# Bradford, the usual cone response for chromatic adaptation, and its inverse.
_BRADFORD = (
    (0.8951, 0.2664, -0.1614),
    (-0.7502, 1.7135, 0.0367),
    (0.0389, -0.0685, 1.0296),
)
_BRADFORD_INV = (
    (0.9869929, -0.1470543, 0.1599627),
    (0.4323053, 0.5183603, 0.0492912),
    (-0.0085287, 0.0400428, 0.9684867),
)

# XYZ (D65) to linear sRGB.
_XYZ_TO_RGB = (
    (3.2404542, -1.5371385, -0.4985314),
    (-0.9692660, 1.8760108, 0.0415560),
    (0.0556434, -0.2040259, 1.0572252),
)


def _mul(matrix, vec) -> tuple:
    return tuple(sum(m * v for m, v in zip(row, vec)) for row in matrix)


def _xy_to_xyz(x: float, y: float, big_y: float = 1.0) -> tuple:
    """xyY to XYZ. y is a denominator, so a zero is refused rather than divided by."""
    if y <= 0:
        raise ValueError(f"chromaticity y must be positive, got {y}")
    return (x * big_y / y, big_y, (1.0 - x - y) * big_y / y)


def adapt_to_d65(xyz: tuple, source_white_xy: tuple) -> tuple:
    """Bradford-adapt `xyz`, measured under `source_white_xy`, to a D65 viewer.

    🔴 WITHOUT THIS EVERY FILTER COMES OUT ORANGE, including the clear ones.
    sRGB is defined against D65 and most of this data is measured under tungsten,
    so feeding the measured XYZ straight to the sRGB matrix renders the SOURCE's
    colour on top of the filter's. A clear filter under illuminant A would be a
    strong amber and look exactly like a bug.

    ⭐ Adapting instead answers the question a designer is actually asking — what
    does this filter DO to the light — which is also what a renderer needs, since
    it applies the lamp's own colour separately. Doing both would count the
    tungsten twice.
    """
    src = _mul(_BRADFORD, _xy_to_xyz(*source_white_xy))
    dst = _mul(_BRADFORD, _xy_to_xyz(*_D65))
    cone = _mul(_BRADFORD, xyz)
    scaled = tuple(c * (d / s) for c, s, d in zip(cone, src, dst))
    return _mul(_BRADFORD_INV, scaled)


def _gamma(c: float) -> float:
    """Linear light to an sRGB value, 0-1. The piecewise IEC 61966-2-1 curve."""
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def srgb_from_xy(x: float, y: float, illuminant: str) -> Dict[str, Any]:
    """The filter's own colour as sRGB, at full value.

    ⚠ LUMINANCE IS DELIBERATELY NOT APPLIED. The measured Y is returned beside the
    colour instead of baked into it, because a 24%-transmission gel rendered at its
    true Y is nearly black and useless as a swatch — while a renderer that wants
    true appearance can multiply, and one that wants a hue cannot un-multiply.
    ➡ So: hue at full value here, `luminance_pct` alongside, policy left to the
    caller.

    🔴 FULL VALUE MEANS SCALING THE BRIGHTEST CHANNEL TO 1, NOT SETTING Y TO 1.
    Asking for a saturated chromaticity at the luminance of white is asking for a
    colour no display can make: every channel lands outside the gamut, clamping
    crushes them to the extremes, and the hue is destroyed. The first version of
    this did exactly that and rendered R80 Primary Blue as pure cyan.
    ➡ Convert at any luminance, then divide through by the largest channel. Hue and
    saturation survive and the result is in range by construction.

    ⚠ OUT OF GAMUT IS REPORTED, NOT HIDDEN, and it means a NEGATIVE channel — a
    chromaticity outside sRGB's three primaries, which no scaling can bring in.
    Many real filters are more saturated than a monitor, so this is common rather
    than exceptional. The negative is clamped, because a hex value has nothing else
    to offer, and the flag lets a consumer tell "this is the colour" from "this is
    as close as sRGB gets".
    """
    white = _WHITE_XY.get(illuminant)
    if white is None:
        raise KeyError(f"no white point for illuminant {illuminant!r}")
    linear = _mul(_XYZ_TO_RGB, adapt_to_d65(_xy_to_xyz(x, y), white))
    out_of_gamut = any(c < -1e-6 for c in linear)
    positive = [max(0.0, c) for c in linear]
    peak = max(positive)
    # ⚠ A chromaticity that maps to no positive channel at all has no hue to show.
    # Nothing in the data does this; the guard is here so it cannot divide by zero.
    scaled = [c / peak for c in positive] if peak > 0 else [0.0, 0.0, 0.0]
    rgb = [int(round(_gamma(c) * 255)) for c in scaled]
    return {
        "hex": "#%02X%02X%02X" % tuple(rgb),
        "rgb": rgb,
        "out_of_gamut": out_of_gamut,
    }


def load_gel_colour(path=None) -> Dict[str, Dict[str, Any]]:
    """gel_colour.csv beside this file, one entry per gel, best illuminant chosen.

    ⚠ Rows whose chromaticity will not convert are DROPPED rather than guessed at,
    and a gel left with no usable row simply has no colour — see `colour_for`.
    """
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "gel_colour.csv")
    best: Dict[str, Dict[str, Any]] = {}
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            illum = (row.get("illuminant") or "").strip()
            if illum not in ILLUMINANT_PREFERENCE:
                continue
            try:
                x, y, big_y = float(row["x"]), float(row["y"]), float(row["Y"])
                colour = srgb_from_xy(x, y, illum)
            except (ValueError, KeyError, TypeError):
                continue
            key = gel_key(row["gel"])
            rank = ILLUMINANT_PREFERENCE.index(illum)
            if key in best and best[key]["_rank"] <= rank:
                continue
            best[key] = {
                "_rank": rank,
                "hex": colour["hex"],
                "rgb": colour["rgb"],
                "out_of_gamut": colour["out_of_gamut"],
                "luminance_pct": big_y,
                "x": x,
                "y": y,
                "illuminant": illum,
                "illuminant_as_published": (row.get("illuminant_as_published") or "").strip(),
                "cct_k": int(row["cct_k"]) if (row.get("cct_k") or "").strip().isdigit() else None,
                "source": row.get("source", ""),
                "source_url": row.get("source_url", ""),
                "retrieved": row.get("retrieved", ""),
            }
    for entry in best.values():
        del entry["_rank"]
    return best


GEL_COLOUR = load_gel_colour()


def colour_for(gel: str) -> Optional[Dict[str, Any]]:
    """The colour for one gel code, or None where none is published.

    🔴 NONE, NEVER A FALLBACK. #148 is explicit: *"the absence is currently visible
    and a wrong value would not be"* — and the bug that started all of this was a
    renderer quietly substituting warm white for thirteen filters it did not know.
    A caller that wants a default can choose one; this will not choose it for them.
    """
    return GEL_COLOUR.get(gel_key(gel))
