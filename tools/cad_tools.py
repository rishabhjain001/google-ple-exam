"""
CAD / Drawing Inspection Helpers
=================================
Utilities for inspecting .dxf and 2D/3D geometry files.
"""

from pathlib import Path
from typing import Any


def inspect_dxf(filepath: str) -> dict[str, Any]:
    """
    Extract layers, block names, and bounding boxes from a DXF file.
    """
    try:
        import ezdxf
        doc = ezdxf.readfile(filepath)
        msp = doc.modelspace()

        layers = [layer.dxf.name for layer in doc.layers]
        blocks = [block.name for block in doc.blocks]

        entity_counts = {}
        for entity in msp:
            e_type = entity.dxftype()
            entity_counts[e_type] = entity_counts.get(e_type, 0) + 1

        return {
            "file": filepath,
            "layers": layers,
            "blocks": blocks[:30],
            "entity_counts": entity_counts,
        }
    except Exception as e:
        return {"error": f"Failed to inspect DXF: {e}"}
