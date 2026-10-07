"""GUI-only ground appearance helpers.

The physics ground remains ``/World/ground``.  This module adds a separate
visual mesh without collision, so playback can show contact clearly without
changing training or evaluation physics.
"""


def _mesh(stage, path, vertices, faces):
    from pxr import UsdGeom, Vt

    mesh = UsdGeom.Mesh.Define(stage, path)
    mesh.CreatePointsAttr(Vt.Vec3fArray(vertices))
    mesh.CreateFaceVertexCountsAttr(Vt.IntArray([4] * len(faces)))
    mesh.CreateFaceVertexIndicesAttr(Vt.IntArray([index for face in faces for index in face]))
    mesh.CreateSubdivisionSchemeAttr("none")
    return mesh


def _material(stage, path, *, color, metallic, roughness):
    import isaaclab.sim as sim_utils

    cfg = sim_utils.PreviewSurfaceCfg(
        diffuse_color=color,
        metallic=metallic,
        roughness=roughness,
    )
    cfg.func(path, cfg)
    return path


def apply(stage, *, style="grid", extent_m=128.0, grid_spacing_m=1.0):
    """Add a colored/grid visual layer above the physical plane.

    Returns a small identity dictionary for the GUI result.  The generated
    prims deliberately have no CollisionAPI or rigid-body API.
    """
    from pxr import UsdGeom
    import isaaclab.sim as sim_utils

    root_path = "/World/native_gui_ground_visual"
    if stage.GetPrimAtPath(root_path).IsValid():
        stage.RemovePrim(root_path)
    if style == "none":
        return {"style": "none", "collision": False}
    if style not in ("grid", "solid"):
        raise ValueError(f"unknown ground visual style: {style}")
    if extent_m <= 0 or grid_spacing_m <= 0:
        raise ValueError("extent and grid spacing must be positive")

    # Keep the visual layer a fraction above z=0 to avoid z-fighting with the
    # physical Plane.  This offset is visual only and does not move the robot.
    half = float(extent_m) / 2.0
    base_z = 0.00025
    base = _mesh(
        stage,
        f"{root_path}/base",
        [(-half, -half, base_z), (half, -half, base_z),
         (half, half, base_z), (-half, half, base_z)],
        [(0, 1, 2, 3)],
    )
    base_material = _material(
        stage,
        f"{root_path}/base_material",
        color=(0.16, 0.20, 0.24),
        metallic=0.18,
        roughness=0.62,
    )
    sim_utils.bind_visual_material(base.GetPrim().GetPath(), base_material, stage=stage)

    if style == "solid":
        return {"style": "solid", "collision": False, "extent_m": extent_m}

    # One mesh contains all grid quads.  At this scale the few hundred quads
    # are substantially cheaper and more reliable than spawning many cubes.
    line_width = min(0.012, float(grid_spacing_m) * 0.04)
    z = base_z + 0.00025
    vertices = []
    faces = []

    def add_quad(x0, y0, x1, y1):
        start = len(vertices)
        vertices.extend(((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)))
        faces.append((start, start + 1, start + 2, start + 3))

    count = int(extent_m / grid_spacing_m)
    for index in range(count + 1):
        coordinate = -half + index * grid_spacing_m
        add_quad(coordinate - line_width / 2, -half,
                 coordinate + line_width / 2, half)
        add_quad(-half, coordinate - line_width / 2,
                 half, coordinate + line_width / 2)
    grid = _mesh(stage, f"{root_path}/grid", vertices, faces)
    grid_material = _material(
        stage,
        f"{root_path}/grid_material",
        color=(0.62, 0.72, 0.78),
        metallic=0.08,
        roughness=0.35,
    )
    sim_utils.bind_visual_material(grid.GetPrim().GetPath(), grid_material, stage=stage)
    return {
        "style": "grid",
        "collision": False,
        "extent_m": extent_m,
        "grid_spacing_m": grid_spacing_m,
        "grid_quads": len(faces),
    }


def add_lighting(stage):
    """Add a neutral dome light only when playback has no authored dome light."""
    import isaaclab.sim as sim_utils

    path = "/World/native_gui_dome_light"
    if not stage.GetPrimAtPath(path).IsValid():
        cfg = sim_utils.DomeLightCfg(intensity=1800.0, color=(0.82, 0.87, 0.92))
        cfg.func(path, cfg)
    return {"path": path, "intensity": 1800.0}
