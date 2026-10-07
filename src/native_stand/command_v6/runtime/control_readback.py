"""Runtime-only ownership and physical limit readback."""
from native_stand.control_readback import check_control


def verify(env):
    result=check_control(env)
    if not result["active_gain_zero"] or not result["active_effort_limits_match"]:
        raise RuntimeError("active controller ownership or effort limits differ")
    return result


def verify_ground(env, spec):
    from pxr import UsdGeom, UsdPhysics
    stage=env.sim.stage
    prim=stage.GetPrimAtPath("/World/ground")
    plane=UsdGeom.Plane(prim)
    if not prim.IsValid() or not plane or not prim.HasAPI(UsdPhysics.CollisionAPI):
        raise RuntimeError("Ground must be one collision-enabled USD Plane")
    binding=[str(path) for path in prim.GetRelationship("material:binding:physics").GetTargets()]
    expected=spec["ground"]["material_path"]
    if binding!=[expected]:
        raise RuntimeError("Plane physical material binding differs")
    material=stage.GetPrimAtPath(expected)
    fields={"static_friction":"physics:staticFriction",
            "dynamic_friction":"physics:dynamicFriction",
            "restitution":"physics:restitution"}
    values={key:material.GetAttribute(attribute).Get() for key,attribute in fields.items()}
    if any(values[key] is None or abs(values[key]-spec["ground"][key])>1e-6 for key in fields):
        raise RuntimeError("Composed plane material differs from spec")
    if (plane.GetAxisAttr().Get()!="Z" or
            abs(plane.GetWidthAttr().Get()-spec["ground"]["width_m"])>1e-6 or
            abs(plane.GetLengthAttr().Get()-spec["ground"]["length_m"])>1e-6):
        raise RuntimeError("Plane normal or extent differs from spec")
    height=float(UsdGeom.Xformable(prim).GetLocalTransformation().ExtractTranslation()[2])
    if abs(height-spec["ground"]["height_m"])>1e-6:
        raise RuntimeError("Plane height differs from spec")
    return {"collider":"USD Plane","path":"/World/ground","axis":"Z",
            "material_binding":binding,"composed_material":values,
            "height_m":height,
            "width_m":plane.GetWidthAttr().Get(),"length_m":plane.GetLengthAttr().Get(),
            "physx_effective_contact_offset":"UNKNOWN",
            "physx_effective_rest_offset":"UNKNOWN"}
