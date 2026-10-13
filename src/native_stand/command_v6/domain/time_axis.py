"""Explicit policy sample clocks; index boundaries differ from post-step timestamps."""
import math


def interval(start,stop,*,dt,total_samples):
    if (type(start) is not int or type(stop) is not int or not 0<=start<=stop<=total_samples
            or not math.isfinite(dt) or dt<=0):raise ValueError('invalid half-open sample interval')
    return {'index_half_open':[start,stop],'boundary_seconds':[start*dt,stop*dt],
        'first_post_step_seconds':(start+1)*dt if stop>start else None,
        'last_post_step_seconds':stop*dt if stop>start else None,'duration_s':(stop-start)*dt,
        'sample_rate_hz':1/dt,'clock':'policy trace; reset sample excluded'}


def event(index,*,dt,recovery_seconds,initialization_seconds=None):
    if type(index) is not int or index<0 or not math.isfinite(dt) or dt<=0:
        raise ValueError('invalid trace index/time step')
    if not math.isfinite(recovery_seconds) or recovery_seconds<0:raise ValueError('invalid recovery clock')
    if initialization_seconds is not None and (not math.isfinite(initialization_seconds) or initialization_seconds<0):
        raise ValueError('invalid initialization duration')
    return {'trace_index':index,'trace_boundary_s':index*dt,'trace_post_step_s':(index+1)*dt,
        'recovery_clock_s':recovery_seconds,'initialization_duration_s':initialization_seconds,
        'clock_note':'recovery clock read from trace; initialization UNKNOWN unless supplied'}


def sustained_events(mask,*,dt):
    events=[];start=None
    for i,value in enumerate([*mask,False]):
        if value and start is None:start=i
        if not value and start is not None:
            events.append(interval(start,i,dt=dt,total_samples=len(mask)));start=None
    return events


WINDOW_VERSION='policy_post_step_closed_v1'


def window_indices(total_samples, *, dt, window_s, version=WINDOW_VERSION):
    """Float64 gate convention: post-step t=(i+1)dt, closed [start,end].

    Do not silently reinterpret archived summaries calculated on another axis.
    """
    if version!=WINDOW_VERSION:raise ValueError('unsupported window version')
    if (type(total_samples) is not int or total_samples<0 or not math.isfinite(dt) or dt<=0
            or len(window_s)!=2 or any(not math.isfinite(t) for t in window_s)
            or not 0<=window_s[0]<window_s[1]):raise ValueError('invalid policy window')
    start,end=window_s
    first=max(0,math.ceil((start-1e-8)/dt)-1)
    stop=max(first,math.floor((end+1e-8)/dt))
    actual_stop=min(stop,total_samples);actual_first=min(first,total_samples)
    return {'version':version,'index_half_open':[actual_first,actual_stop],
        'required_index_half_open':[first,stop],'required_samples':stop-first,
        'observed_samples':actual_stop-actual_first,'complete':total_samples>=stop,
        'window_s':list(window_s),'dt_s':dt,'clock':'post-step; closed endpoints; float64 gate convention'}
