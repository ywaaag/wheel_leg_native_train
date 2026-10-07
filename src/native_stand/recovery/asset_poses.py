"""Offline USD joint-frame closure and ideal collider support geometry.

This prepares explicit pose candidates, not a controller or a virtual-leg map.
Authored geometry does not certify runtime penetration or solver convergence.
"""
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation


def transform(position, quaternion):
    q = quaternion
    matrix = np.eye(4)
    matrix[:3,:3] = Rotation.from_quat([*q.GetImaginary(),q.GetReal()]).as_matrix()
    matrix[:3,3] = position
    return matrix


def verify_wheel_readback(evaluation, asset, pose_library, *, tolerance_m, samples_per_env=8):
    """CLI/offline boundary: verify runtime pre-reset wheel centers against USD FK."""
    names=('left_hip_pitch','left_active_link_pitch','right_hip_pitch','right_active_link_pitch')
    asset=AssetPoses(asset)
    poses={p['pose_id']:p for p in pose_library['poses']}
    checked=[]
    for episode in evaluation['per_env']:
        rows=episode.get('wheel_geometry_trace_100hz')
        if not rows:raise ValueError('Missing runtime wheel-center evidence')
        q0=poses[episode['pose_id']]['joint_pos']
        for index in np.linspace(0,len(rows)-1,min(len(rows),samples_per_env),dtype=int):
            row=np.asarray(rows[index],dtype=float)
            if row.shape!=(13,) or not np.isfinite(row).all():raise ValueError('Invalid runtime wheel-center evidence')
            q,error=asset.solve(dict(zip(names,row[9:13])),q0)
            bodies=asset.forward(q)
            actual=row[:6].reshape(2,3)
            expected=np.array([bodies[f'{side}_wheel'][:3,3] for side in ('left','right')])
            delta=float(np.linalg.norm(actual-expected,axis=-1).max())
            checked.append({'env_id':episode['env_id'],'policy_index':int(index),
                'center_difference_max_m':delta,'closure_max_m':float(error.max())})
    peak=max((r['center_difference_max_m'] for r in checked),default=float('inf'))
    return {'passed':bool(checked) and peak<=tolerance_m and
            all(r['closure_max_m']<=1e-4 for r in checked),
            'tolerance_m':tolerance_m,'peak_center_difference_m':peak,'samples':checked,
            'scope':'Physical pre-reset main-wheel body origins in root coordinates versus authored USD closure branch, not contact patches.'}


class AssetPoses:
    def __init__(self, path):
        from pxr import Usd, UsdGeom, UsdPhysics
        self.stage = Usd.Stage.Open(str(path))
        cache = UsdGeom.XformCache()
        self.joints = []
        self.loops = []
        self.colliders = []
        self.bodies = {p.GetName():p for p in self.stage.Traverse() if p.HasAPI(UsdPhysics.RigidBodyAPI)}
        for prim in self.stage.Traverse():
            if prim.IsA(UsdPhysics.Joint):
                joint = UsdPhysics.Joint(prim)
                a,b = joint.GetBody0Rel().GetTargets(),joint.GetBody1Rel().GetTargets()
                if not a or not b:
                    continue
                record = {'name':prim.GetName(),'a':str(a[0]).split('/')[-1],
                    'b':str(b[0]).split('/')[-1],
                    'ta':transform(joint.GetLocalPos0Attr().Get(),joint.GetLocalRot0Attr().Get()),
                    'tb':transform(joint.GetLocalPos1Attr().Get(),joint.GetLocalRot1Attr().Get())}
                if prim.IsA(UsdPhysics.RevoluteJoint):
                    revolute = UsdPhysics.RevoluteJoint(prim)
                    record.update(axis='XYZ'.index(revolute.GetAxisAttr().Get()),
                        limits=np.deg2rad([revolute.GetLowerLimitAttr().Get(),revolute.GetUpperLimitAttr().Get()]).tolist())
                    self.joints.append(record)
                elif prim.IsA(UsdPhysics.SphericalJoint):
                    self.loops.append(record)
            if prim.HasAPI(UsdPhysics.CollisionAPI):
                body = prim.GetParent()
                while body and body.GetName() not in self.bodies:
                    body = body.GetParent()
                if not body:
                    raise ValueError(f'Collider without rigid body: {prim.GetPath()}')
                world = np.asarray(cache.GetLocalToWorldTransform(prim)).T
                parent = np.asarray(cache.GetLocalToWorldTransform(body)).T
                local = np.linalg.inv(parent) @ world
                shape = {'path':str(prim.GetPath()),'body':body.GetName(),'matrix':local,
                         'type':prim.GetTypeName()}
                for name in ('radius','height','size','axis'):
                    attr = prim.GetAttribute(name)
                    if attr and attr.Get() is not None:
                        shape[name] = attr.Get()
                self.colliders.append(shape)

    def forward(self, q):
        out = {'robot':np.eye(4)}
        pending = list(self.joints)
        while pending:
            next_pending = []
            for joint in pending:
                if joint['a'] not in out:
                    next_pending.append(joint)
                    continue
                rotation = np.eye(4)
                vector = np.zeros(3);vector[joint['axis']] = q.get(joint['name'],0.)
                rotation[:3,:3] = Rotation.from_rotvec(vector).as_matrix()
                out[joint['b']] = out[joint['a']] @ joint['ta'] @ rotation @ np.linalg.inv(joint['tb'])
            if len(next_pending)==len(pending):
                raise ValueError('Joint tree is disconnected or cyclic')
            pending = next_pending
        return out

    def residual(self, q, side=None):
        bodies = self.forward(q)
        values = []
        for loop in self.loops:
            if side is None or loop['name'].startswith(side):
                values.extend((bodies[loop['a']] @ loop['ta'])[:3,3]-(bodies[loop['b']] @ loop['tb'])[:3,3])
        return np.asarray(values)

    def solve(self, active, initial=None):
        q = {j['name']:0. for j in self.joints}
        q.update(initial or {});q.update(active)
        for side in ('left','right'):
            passive = [f'{side}_{part}_pitch' for part in ('long_link','node_link','parallel_link','knee')]
            records = {j['name']:j for j in self.joints}
            lo,hi = np.array([records[n]['limits'] for n in passive]).T
            def residual(values):
                candidate = dict(q);candidate.update(zip(passive,values))
                return self.residual(candidate,side)
            result = least_squares(residual,np.array([q[n] for n in passive]).clip(lo+1e-8,hi-1e-8),
                bounds=(lo,hi),xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=200)
            q.update(zip(passive,result.x))
        error = np.linalg.norm(self.residual(q).reshape(-1,3),axis=-1)
        return q,error

    def support(self, q, root_rotation):
        """Ideal collider lowest points, including scale and axle orientation."""
        bodies = self.forward(q)
        rows = []
        for shape in self.colliders:
            matrix = root_rotation @ bodies[shape['body']] @ shape['matrix']
            normal = matrix[2,:3]
            kind = shape['type']
            if kind=='Cube':
                extent = np.abs(normal).sum()*float(shape['size'])/2
            elif kind=='Sphere':
                extent = np.linalg.norm(normal)*float(shape['radius'])
            elif kind in ('Cylinder','Capsule'):
                axis = 'XYZ'.index(shape['axis'])
                axial = abs(normal[axis])*float(shape['height'])/2
                radial = float(shape['radius'])*(np.linalg.norm(normal) if kind=='Capsule'
                    else np.linalg.norm(np.delete(normal,axis)))
                extent = axial+radial
            else:
                raise ValueError(f'Unsupported collision geometry: {kind}')
            rows.append({'path':shape['path'],'body':shape['body'],
                         'lowest_z_root':float(matrix[2,3]-extent)})
        return rows
