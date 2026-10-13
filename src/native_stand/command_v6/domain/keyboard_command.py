"""Explicit keyboard targets and bounded command ramps, without runtime IO."""
import math


class KeyboardCommand:
    def __init__(self, speed=.1, yaw_speed=.1, acceleration=.5, yaw_acceleration=1., max_speed=4., max_yaw_speed=4.):
        if not all(math.isfinite(x) for x in (speed,yaw_speed,acceleration,yaw_acceleration,max_speed,max_yaw_speed)):
            raise ValueError('Command limits must be finite')
        if not 0<max_speed<=4 or not 0<=max_yaw_speed<=4 or not 0<=speed<=max_speed or not 0<=yaw_speed<=max_yaw_speed or acceleration<=0 or yaw_acceleration<=0:
            raise ValueError('Initial speeds must fit configured GUI limits, each maximum<=4')
        self.max_speed=max_speed
        self.max_yaw_speed=max_yaw_speed
        self.speed=speed
        self.yaw_speed=yaw_speed
        self.acceleration=acceleration
        self.yaw_acceleration=yaw_acceleration
        self.pressed=set()
        self.current=[0.,0.]
        self.reset_requested=False
        self.stop=False

    def event(self,name,pressed):
        name=name.upper().removeprefix('KEY_')
        name={'UP_ARROW':'UP','DOWN_ARROW':'DOWN','LEFT_ARROW':'LEFT','RIGHT_ARROW':'RIGHT',
              'ARROW_UP':'UP','ARROW_DOWN':'DOWN','ARROW_LEFT':'LEFT','ARROW_RIGHT':'RIGHT'}.get(name,name)
        if pressed:
            if name in ('UP','DOWN'):
                self.speed=round(max(0.,min(self.max_speed,self.speed+(.02 if name=='UP' else -.02))),3)
            elif name in ('LEFT','RIGHT'):
                self.yaw_speed=round(max(0.,min(self.max_yaw_speed,self.yaw_speed+(.02 if name=='RIGHT' else -.02))),3)
            elif name=='SPACE': self.pressed.clear()
            elif name=='R': self.reset_requested=True; self.pressed.clear()
            elif name=='ESCAPE': self.stop=True
            else: self.pressed.add(name)
        else: self.pressed.discard(name)

    def target(self):
        yaw=(int('A' in self.pressed)-int('D' in self.pressed))*self.yaw_speed
        vx=(int('W' in self.pressed)-int('S' in self.pressed))*self.speed
        return [0. if yaw else vx,yaw]

    def advance(self,dt):
        if not math.isfinite(dt) or dt<=0: raise ValueError('Positive finite policy dt required')
        for i,(target,rate) in enumerate(zip(self.target(),(self.acceleration,self.yaw_acceleration))):
            delta=target-self.current[i]
            self.current[i]+=max(-rate*dt,min(rate*dt,delta))
        return self.current[:]

    def reset(self):
        self.pressed.clear()
        self.current=[0.,0.]
        self.reset_requested=False


def synchronize_observation(observation, history, command):
    """Patch only the newest frame command before inference; no history shift."""
    scaled = history.new_tensor(command) * history.new_tensor([2., .25])
    observation['policy'][:,6:8] = scaled
    observation['history'][:,-19:-17] = scaled
    history[:,-19:-17] = scaled
