"""First-episode tensor-buffer evaluation, independent of Isaac and PPO."""
import math
import torch
from .contract import EFFORT_LIMITS

FIELDS = ("root_x","root_y","root_z","vx","vy","yaw","command_vx","command_yaw",
          "left_contact","right_contact","effort_l0","effort_l1","effort_lw",
          "effort_r0","effort_r1","effort_rw","closure","tilt")
CAUSES = ("nonfinite","closure","height","tilt","body_contact","joint_safety")


class EpisodeBuffer:
    def __init__(self, max_steps, num_envs, device, dt=.01):
        self.rows = torch.empty(max_steps,num_envs,len(FIELDS),device=device)
        self.valid = torch.zeros(max_steps,num_envs,dtype=torch.bool,device=device)
        self.done = torch.zeros_like(self.valid)
        self.causes = torch.zeros(num_envs,len(CAUSES),dtype=torch.bool,device=device)
        self.timeout = torch.zeros(num_envs,dtype=torch.bool,device=device)
        self.active = torch.ones(num_envs,dtype=torch.bool,device=device)
        self.dt = dt
        self.index = 0

    def append(self, state, done, snapshots):
        if self.index >= self.rows.shape[0] or state.shape != self.rows.shape[1:] or done.shape != self.active.shape:
            raise ValueError("evaluation sample shape or capacity differs")
        row = state.clone()
        newly_done = done & self.active
        for env_id in torch.nonzero(newly_done,as_tuple=False).flatten().tolist():
            snapshot = snapshots[env_id]
            if snapshot is None:
                raise ValueError(f"env {env_id} missing pre-reset terminal snapshot")
            row[env_id] = row.new_tensor((
                *snapshot["root_pos_w"],snapshot["vx_mps"],snapshot["vy_mps"],
                snapshot["yaw_rad_s"],state[env_id,6],state[env_id,7],
                *snapshot["wheel_contact_n"],*snapshot["effort_nm"],
                max(snapshot["closure_each_m"]),
                math.acos(max(-1.,min(1.,snapshot["up_cos"])))))
            self.causes[env_id] = torch.tensor([bool(snapshot["causes"][name])
                for name in CAUSES],device=row.device)
            self.timeout[env_id] = bool(snapshot["time_out"])
        self.rows[self.index].copy_(row)
        self.valid[self.index].copy_(self.active)
        self.done[self.index].copy_(newly_done)
        self.active &= ~done
        self.index += 1

    def packed(self):
        return (self.rows[:self.index].cpu(),self.valid[:self.index].cpu(),
                self.done[:self.index].cpu(),self.causes.cpu(),self.timeout.cpu())


def score(rows, valid, done, causes, timeout, *, dt, target_window=(1.,4.),
          requested_steps=None, full_trace=False, effective_protocol=None):
    if rows.ndim!=3 or rows.shape[-1]!=len(FIELDS) or valid.shape!=rows.shape[:2]:
        raise ValueError("evaluation tensor dimensions differ")
    if requested_steps is not None and requested_steps<1:
        raise ValueError("requested evaluation window must contain steps")
    results = []
    limits = rows.new_tensor(EFFORT_LIMITS)
    for env_id in range(rows.shape[1]):
        sample = rows[valid[:,env_id],env_id]
        if len(sample)==0:
            results.append({"env_id":env_id,"outcome":"UNKNOWN","reason":"no first-episode data"})
            continue
        count = len(sample)
        failure = [name for name,on in zip(CAUSES,causes[env_id].tolist()) if on]
        if failure and any(name in ("nonfinite","closure") for name in failure):
            outcome="runtime_fault"
        elif failure:
            outcome="task_failure"
        elif (bool(timeout[env_id]) and bool(done[count-1,env_id]) and
              (requested_steps is None or count>=requested_steps)):
            outcome="completed"
        elif requested_steps is not None and count>=requested_steps and not bool(done[count-1,env_id]):
            outcome="completed"
        else:
            outcome="UNKNOWN"
        completion_reason=("time_limit" if bool(timeout[env_id]) and outcome=="completed" else
                           "evaluation_window" if outcome=="completed" else "unknown")
        if outcome=="UNKNOWN" and bool(timeout[env_id]):
            completion_reason="early_time_limit"
        xy = sample[:,:2]
        displacement = torch.linalg.vector_norm(xy-xy[0],dim=-1)
        time = torch.arange(1,count+1,dtype=torch.float64,device=sample.device)*dt
        from .time_axis import window_indices
        window_plan=window_indices(count,dt=dt,window_s=target_window)
        lo,hi=window_plan['index_half_open']
        window=torch.zeros(count,dtype=torch.bool,device=sample.device);window[lo:hi]=True
        steady = window if effective_protocol is not None else time>=2.
        parking=(time>=9.) if effective_protocol is None else torch.zeros_like(time,dtype=torch.bool)
        if effective_protocol is not None and effective_protocol.get('parking_window_s'):
            start,end=effective_protocol['parking_window_s']
            parking=(time>=start)&(time<=end)
        saturation = (sample[:,10:16].abs()>=limits-1e-4).any(-1)
        def optional_mean(values, mask):
            return float(values[mask].mean()) if bool(mask.any()) else None
        row = {"env_id":env_id,"outcome":outcome,
            "termination_reason":"+".join(failure) if failure else completion_reason,
            "continuous_s":count*dt,"initial_root_xy_m":xy[0].tolist(),
            "final_root_xy_m":xy[-1].tolist(),"net_drift_m":float(displacement[-1]),
            "max_excursion_m":float(displacement.max()),
            "dual_contact_fraction":float(((sample[:,8:10]>2.).all(-1)).float().mean()),
            "window_time_axis":window_plan,
            "mean_abs_vx_error_mps":optional_mean((sample[:,3]-sample[:,6]).abs(),window),
            "mean_abs_yaw_error_rad_s":optional_mean((sample[:,5]-sample[:,7]).abs(),window),
            "mean_abs_vx_mps":optional_mean(sample[:,3].abs(),window),
            "abs_mean_vx_mps":abs(optional_mean(sample[:,3],window)) if bool(window.any()) else None,
            "height_steady_mean_m":optional_mean(sample[:,2],steady),
            "height_min_m":float(sample[:,2].min()),
            "peak_tilt_rad":float(sample[:,17].max()),
            "closure_max_m":float(sample[:,16].max()),
            "saturation_fraction":float(saturation.float().mean())}
        row.update(mean_abs_vy_mps=optional_mean(sample[:,4].abs(),window),
            mean_vx_mps=optional_mean(sample[:,3],window),
            mean_yaw_rad_s=optional_mean(sample[:,5],window),
            height_steady_end_m=float(sample[-1,2]),
            height_steady_fraction=(optional_mean(((sample[:,2]>=.38)&(sample[:,2]<=.42)).float(),steady)),
            vx_direction_fraction=optional_mean((sample[:,3]*sample[:,6]>0).float(),window),
            yaw_direction_fraction=optional_mean((sample[:,5]*sample[:,7]>0).float(),window),
            stop_vx_abs_mps=optional_mean(sample[:,3].abs(),parking),
            stop_yaw_abs_rad_s=optional_mean(sample[:,5].abs(),parking))
        if full_trace:
            row["trace"] = sample.tolist()
        results.append(row)
    return {"fields":FIELDS,"per_env":results,
            "outcome_counts":{kind:sum(row["outcome"]==kind for row in results)
                              for kind in ("completed","task_failure","runtime_fault","UNKNOWN")},
            "dt":dt,"trace_retained":full_trace}


def standing_gate(result, protocol):
    """Score full zero-command episodes; missing metrics fail their own checks."""
    scored=protocol["scored_envs"]
    checks=[]
    for row in result["per_env"]:
        def metric(name):
            value=row.get(name)
            return float(value) if value is not None and math.isfinite(float(value)) else None

        failed=[]
        if row.get("outcome")!="completed" or metric("continuous_s") is None or metric("continuous_s")<protocol["seconds"]-.01:
            failed.append("continuous")
        low_speed_zero = protocol.get("zero_mode") == "low_speed"
        limits=(("net_drift_m","standing_drift_max_m"),
                ("max_excursion_m","standing_excursion_max_m"),
                ("closure_max_m","closure_max_m"),
                ("peak_tilt_rad","peak_tilt_max_rad"),
                ("saturation_fraction","saturation_fraction_max"),
                ("mean_abs_vx_error_mps","vx_error_max_mps"),
                ("mean_abs_yaw_error_rad_s","yaw_error_max_rad_s"))
        for field,threshold in limits:
            if low_speed_zero and field in ("net_drift_m","max_excursion_m","mean_abs_vx_error_mps"):
                continue
            value=metric(field)
            if value is None or value>protocol[threshold]:
                failed.append(field)
        if low_speed_zero:
            value=metric("mean_abs_vx_mps")
            if value is None or value>protocol.get("zero_mean_abs_vx_max_mps",.5):
                failed.append("zero_mean_abs_vx_mps")
        contact=metric("dual_contact_fraction")
        if contact is None or contact<protocol["dual_contact_min"]:
            failed.append("dual_contact_fraction")
        height=metric("height_steady_mean_m")
        low,high=protocol["standing_height_m"]
        if height is None or not low<=height<=high:
            failed.append("height_steady_mean_m")
        for field,threshold in (("mean_abs_vy_mps","vy_abs_max_mps"),):
            if threshold in protocol and (metric(field) is None or metric(field)>protocol[threshold]):
                failed.append(field)
        if 'height_steady_fraction_min' in protocol and (metric('height_steady_fraction') is None or metric('height_steady_fraction')<protocol['height_steady_fraction_min']):
            failed.append('height_steady_fraction')
        checks.append({"env_id":row.get("env_id"),"outcome":row.get("outcome"),
                       "accepted":not failed,"failed_checks":failed})
    passed=sum(row["accepted"] for row in checks)
    return {"accepted":len(checks)==scored and passed==scored,
            "passed_envs":passed,"scored_envs":scored,"per_env":checks}


def motion_gate(result, target, protocol):
    # Physical/support checks share the standing gate; translational movement is expected.
    limits={**protocol,'standing_drift_max_m':100.,'standing_excursion_max_m':100.}
    gate=standing_gate(result,limits)
    for row,check in zip(result['per_env'],gate['per_env']):
        axis='vx' if target[0] else 'yaw'
        mean=row.get('mean_vx_mps' if axis=='vx' else 'mean_yaw_rad_s')
        fraction=row.get(axis+'_direction_fraction')
        if mean is None or mean*target[0 if axis=='vx' else 1]<=0 or fraction is None or fraction<.9:
            check['failed_checks'].append('command_direction')
        if protocol.get('stop_window_s', 0.) > 0.:
            for name,bound in (('stop_vx_abs_mps',.02),('stop_yaw_abs_rad_s',.03)):
                if row.get(name) is None or row[name]>bound:
                    check['failed_checks'].append(name)
        check['accepted']=not check['failed_checks']
    gate['passed_envs']=sum(x['accepted'] for x in gate['per_env'])
    gate['accepted']=gate['passed_envs']==protocol['scored_envs'] and len(gate['per_env'])==protocol['scored_envs']
    return gate


def capability_gate(result, target, protocol):
    """Versioned sustained-motion gate using only the scored episode trace."""
    if protocol.get('protocol_identity') == 'motion_absolute_v3':
        return absolute_motion_gate(result, target, protocol)
    axis = 3 if target[0] else 5
    value = target[0] if target[0] else target[1]
    checks = []
    for row in result['per_env']:
        failed = []
        trace = row.get('trace')
        if row.get('outcome') != 'completed' or row.get('continuous_s',0) < result['seconds']-.01:
            failed.append('continuous')
        if not trace:
            failed.append('missing_trace')
        else:
            sample = torch.as_tensor(trace)
            dt = result['dt']
            time = torch.arange(1,len(sample)+1)*dt
            start,end = (protocol['steady_window_s'] if value == 0 else protocol['motion_window_s'])
            window = sample[(time >= start)&(time <= end)]
            if len(window) == 0:
                failed.append('hold_window')
            elif value == 0:
                horizontal = torch.linalg.vector_norm(window[:,3:5],dim=-1)
                row['horizontal_speed_p95_mps'] = float(torch.quantile(horizontal,.95))
                row['horizontal_speed_mean_mps'] = float(horizontal.mean())
                row['steady_mean_abs_yaw_rad_s'] = float(window[:,5].abs().mean())
                if row['horizontal_speed_p95_mps'] > .3:
                    failed.append('horizontal_speed_p95')
                if row['steady_mean_abs_yaw_rad_s'] > .3:
                    failed.append('zero_yaw')
            else:
                signed = window[:,axis] * (1 if value>0 else -1)
                row['hold_direction_fraction'] = float((signed>0).float().mean())
                row['hold_signed_mean'] = float(signed.mean())
                row['hold_70pct_fraction'] = float((signed>=.7*abs(value)).float().mean())
                if row['hold_direction_fraction'] < .9:
                    failed.append('direction')
                if not .8*abs(value) <= row['hold_signed_mean'] <= 1.2*abs(value):
                    failed.append('hold_speed')
                if row['hold_70pct_fraction'] < .8:
                    failed.append('sustained_fraction')
                if axis == 5:
                    row['hold_horizontal_speed_mean_mps'] = float(torch.linalg.vector_norm(window[:,3:5],dim=-1).mean())
                    if row['hold_horizontal_speed_mean_mps'] > .3:
                        failed.append('yaw_translation')
                if abs(value)>=4:
                    rolling = torch.nn.functional.avg_pool1d(signed[None,None],kernel_size=100,stride=1).flatten()
                    streak = maximum = 0
                    for passed in (rolling>=3.8).tolist():
                        streak = streak+1 if passed else 0
                        maximum = max(maximum,streak)
                    row['continuous_rolling_mean_above_3p8_s'] = maximum*dt
                    if row['hold_signed_mean']<3.6 or row['hold_signed_mean']>4.4 or row['continuous_rolling_mean_above_3p8_s']<3.:
                        failed.append('final_sustained_speed')
                    stopped = sample[time>=26.]
                    if len(stopped) == 0:
                        failed.append('final_zero_window')
                    else:
                        row['final_zero_horizontal_p95_mps'] = float(torch.quantile(torch.linalg.vector_norm(stopped[:,3:5],dim=-1),.95))
                        row['final_zero_mean_abs_yaw_rad_s'] = float(stopped[:,5].abs().mean())
                        if row['final_zero_horizontal_p95_mps']>.3 or row['final_zero_mean_abs_yaw_rad_s']>.3:
                            failed.append('final_zero')
        if row.get('closure_max_m',float('inf')) > protocol['closure_max_m']:
            failed.append('closure')
        if row.get('peak_tilt_rad',float('inf')) > protocol['peak_tilt_max_rad']:
            failed.append('tilt')
        if row.get('dual_contact_fraction',0.) < protocol['dual_contact_min']:
            failed.append('contact')
        if not protocol['standing_height_m'][0] <= row.get('height_steady_mean_m',float('inf')) <= protocol['standing_height_m'][1]:
            failed.append('height')
        checks.append({'env_id':row['env_id'],'outcome':row['outcome'],
                       'accepted':not failed,'failed_checks':failed})
    passed = sum(check['accepted'] for check in checks)
    return {'accepted':len(checks)==protocol['scored_envs'] and passed==protocol['scored_envs'],
            'passed_envs':passed,'scored_envs':protocol['scored_envs'],'per_env':checks}


def absolute_motion_gate(result, target, protocol):
    """User absolute-error protocol; no hidden relative/minimum-speed rule."""
    checks = []
    for row in result['per_env']:
        failed, missing = [], []
        def check(field, bound, lower=False):
            value = row.get(field)
            if value is None or not math.isfinite(float(value)):
                missing.append(field)
                failed.append('MISSING_EVIDENCE:' + field)
            elif (value < bound if lower else value > bound):
                failed.append(field)
        if row.get('outcome') != 'completed':
            failed.append('continuous')
        check('continuous_s', protocol['requested_seconds'] - .01, True)
        for field, bound in (('closure_max_m', protocol['closure_max_m']),
                ('peak_tilt_rad', protocol['peak_tilt_max_rad']),
                ('saturation_fraction', protocol['saturation_fraction_max'])):
            check(field, bound)
        check('dual_contact_fraction', protocol['dual_contact_min'], True)
        low, high = protocol['standing_height_m']
        check('height_steady_mean_m', low, True)
        check('height_steady_mean_m', high)
        check('mean_abs_vy_mps', protocol['vy_abs_max_mps'])
        trace = row.get('trace')
        if not trace:
            missing.append('trace'); failed.append('MISSING_EVIDENCE:trace')
        else:
            sample = torch.as_tensor(trace, dtype=torch.float64)
            start, end = protocol['motion_window_s'] if any(target) else protocol['steady_window_s']
            from .time_axis import window_indices
            hold_plan=window_indices(len(sample),dt=result['dt'],window_s=[start,end])
            lo,hi=hold_plan['index_half_open'];window=sample[lo:hi]
            expected = round((end-start)/result['dt'])
            if len(window) < expected:
                missing.append('full_hold_window'); failed.append('MISSING_EVIDENCE:full_hold_window')
            else:
                axis = 3 if target[0] else 5
                value = target[0] if target[0] else target[1]
                row['hold_mean_abs_error'] = float((window[:,axis]-value).abs().mean())
                if any(target):
                    row['hold_direction_fraction'] = float((window[:,axis]*value > 0).double().mean())
                    row['hold_signed_mean'] = float(window[:,axis].mean()) * (1 if value > 0 else -1)
                    if row['hold_mean_abs_error'] > (protocol['motion_vx_error_max_mps'] if target[0] else protocol['motion_yaw_error_max_rad_s']) + 1e-9:
                        failed.append('hold_absolute_error')
                    if row['hold_direction_fraction'] < protocol['direction_fraction_min']:
                        failed.append('direction')
                    if target[0]:
                        check('mean_abs_yaw_error_rad_s', protocol['straight_yaw_max_rad_s'])
                    else:
                        check('mean_abs_vx_mps', protocol['yaw_translation_max_mps'])
                        check('net_drift_m', protocol['yaw_drift_max_m'])
                        check('max_excursion_m', protocol['yaw_excursion_max_m'])
                else:
                    check('mean_abs_vx_mps', protocol['zero_mean_abs_vx_max_mps'])
                    check('mean_abs_yaw_error_rad_s', protocol['yaw_error_max_rad_s'])
            # Local excursion is a field boundary guard, not a standing-position target.
            check('max_excursion_m', protocol['field_boundary_max_m'])
        checks.append({'env_id': row['env_id'], 'accepted': not failed,
                       'failed_checks': failed, 'missing_fields': missing})
    passed = sum(check['accepted'] for check in checks)
    return {'accepted': len(checks)==protocol['scored_envs'] and passed==protocol['scored_envs'],
            'passed_envs': passed, 'scored_envs': protocol['scored_envs'], 'per_env': checks,
            'scope': '100Hz policy-end effort evidence; not every 5ms PD substep audit'}


def select_best_standing(current,candidate):
    """Prefer full acceptance, then more passing envs and less drift."""
    if candidate is None:
        return current
    if current is None:
        return candidate
    def rank(row):
        drift=row["mean_net_drift_m"]
        return (int(row["accepted"]),row["passed_envs"],
                -drift if drift is not None else float("-inf"))
    return candidate if rank(candidate)>rank(current) else current
