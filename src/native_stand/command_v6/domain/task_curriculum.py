"""Explicit capability confirmation, separate from per-episode time limits."""


class TaskProgression:
    def __init__(self, config):
        self.config=config
        self.stage=config.get('initial_stage',0)
        self.streak=0
        self.zero_failures=0
        self.learned_failures=0
        self.history=[]

    def confirm(self, update, cases, *, episode_length_s=10, new_commands=()):
        zero=next(x for x in cases if x['command']==[0,0])
        zero_pass=zero['gate']['accepted']
        self.zero_failures=0 if zero_pass else self.zero_failures+1
        new={tuple(command) for command in new_commands}
        learned_failed=any(not case['gate']['accepted'] for case in cases
                           if tuple(case['command']) not in new and case['command']!=[0,0])
        self.learned_failures=self.learned_failures+1 if learned_failed else 0
        passed=all(x['gate']['accepted'] for x in cases)
        self.streak=self.streak+1 if passed else 0
        event={'update':update,'stage':self.stage,'passed':passed,
               'zero_pass':zero_pass,'streak':self.streak,'next_stage':self.stage,
               'zero_failures':self.zero_failures,'learned_failures':self.learned_failures,
               'stop':False}
        # New height task may take time to learn; don't call initial inability regression.
        if self.stage>0 and self.zero_failures>=self.config['standing_regression_confirmations']:
            event['stop']=True
        learned_limit=self.config.get('learned_regression_confirmations',
                                      2 if self.config['max_enabled_stage']>1 else 0)
        if learned_limit and self.learned_failures>=learned_limit:
            event['stop']=True
        if (self.streak>=self.config['consecutive_confirmations'] and self.stage<self.config['max_enabled_stage']
                and episode_length_s>=10):
            self.stage+=1
            self.streak=0
            event['next_stage']=self.stage
            event['promoted']=True
        self.history.append(event)
        return event

    def state(self):
        return {'stage':self.stage,'streak':self.streak,'zero_failures':self.zero_failures,
                'learned_failures':self.learned_failures,
                'blocked_after_stage':self.config['max_enabled_stage'],
                'blocked_reason':self.config['blocked_reason']}
