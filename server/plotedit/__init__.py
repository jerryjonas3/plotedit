"""plotedit — the computation half of the light plot editor.

Copied 2026.09.23 from My AI Brain/my-skills/plot, where it was built and tested
against real shows. Every module states its sources; photometric figures come from
ETC datasheets and gel transmissions from Rosco.

    photometrics   throw, elevation, pan, pools, footcandles, gel, wash spacing
    scaled_pdf     architectural-scale PDF, sections, scale bar and 1-inch check
    dxf_bridge     DXF in (venue ground plan) and DXF out
    paperwork      read Lightwright XLSX, Vectorworks SLData XML, .lw6 vocabularies
"""
