"""Robot body (links fixed to base_link) collision points in base_link frame."""
import xml.etree.ElementTree as ET
import numpy as np
import armgeo as A


def body_points():
    root = ET.parse(A.URDF).getroot()
    fixed = {j.find("child").get("link"): A._origin(j) for j in root.findall("joint")
             if j.get("type") == "fixed" and j.find("parent").get("link") == "base_link"}
    names = ["base_link"] + [n for n in fixed if n not in ("arm_base_link",)]
    pts, _ = A.load_link_points(names)
    out = {}
    for n, P in pts.items():
        if len(P) == 0:
            continue
        T = fixed.get(n, np.eye(4))
        out[n] = P @ T[:3, :3].T + T[:3, 3]
    return out
