"""CPU arithmetic for a reward DESIGN, not a trainer/runtime implementation."""
import math,json

def cost(x):return x*x/(1+x*x)

def density(*,h=.34,vx=0.,vy=0.,yaw=0.,pitch=0.,roll=0.,contact_l=20.,contact_r=20.,
            hip=0.,active=0.,offset=0.,leg_difference=0.,omega_pitch=0.,omega_roll=0.,
            effort_normalized_mean_square=0.,target_change_cost=0.):
 """Hypothetical state only; valid control/no physical fault is assumed."""
 if not 0<=effort_normalized_mean_square<=1 or not 0<=target_change_cost<=1:
  raise ValueError('bound check assumes actual effort within limits and bounded target-change cost')
 b=min(1.,max(0.,min(contact_l,contact_r)/2))*min(1.,max(0.,(h-.20)/.10))
 qv=1/(1+(vx*vx+vy*vy)/.30**2+(yaw/.30)**2)
 qp=1/(1+(pitch/.15)**2+(roll/.15)**2)
 gh=1/(1+((h-.34)/.04)**2)
 components={'survival':b,'joint_stationary_upright':5*b*qv*qp,
  'height':1.5*b*qv*gh,'zero_speed':b*qv,
  'mirror':-.20*(cost(hip/.10)+cost(active/.10))/2,
  'wheel':-.30*cost(max(0.,abs(offset)-.01)/.03),
  'length':-.15*cost(leg_difference/.02),
  'angular':-.10*(cost(omega_pitch)+cost(omega_roll))/2,
  'effort':-.02*effort_normalized_mean_square,'target_change':-.002*target_change_cost}
 return {'density':sum(components.values()),'step_reward':.01*sum(components.values()),'components':components}

def check():
 cases={'ideal':{},'slow_lean':{'pitch':.20,'vx':.10},'temporary_correction':{'pitch':.05,'vx':.50},
  'fast_upright':{'vx':2.285},'fast_lean_asymmetric':{'h':.326,'vx':2.285,'pitch':.232,'roll':.205,'hip':.215,'active':.489,'offset':.024,'leg_difference':.0878},
  'no_contact':{'contact_l':0.}}
 result={name:density(**state) for name,state in cases.items()}
 assert math.isclose(result['ideal']['density'],8.5)
 assert result['ideal']['density']>result['temporary_correction']['density']>result['fast_upright']['density']
 assert result['slow_lean']['density']>result['fast_lean_asymmetric']['density']>0
 assert result['no_contact']['density']==0
 for speed in (.1,.3,1.,2.7):
  assert density(vx=speed)==density(vx=-speed)
 assert math.isclose(1-(.20+.30+.15+.10+.02+.002),.228)
 return {'scope':'hypothetical-state CPU arithmetic; no optimizer/physics','maximum_density':8.5,
         'full_support_density_lower_bound_with_effort_in_limits':.228,'cases':result}

if __name__=='__main__':print(json.dumps(check(),indent=2))
