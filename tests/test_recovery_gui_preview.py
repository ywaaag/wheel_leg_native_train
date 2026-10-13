FROZEN_TEST_SCOPE='PORTABLE'
from native_stand.command_v6.tools.play import configure_recovery_preview

def test_single_environment_preview_bypasses_training_64slot_allocation():
    class Env:
        curriculum_training=True
        recovery_config={}
        family="R0"
        def select_initial_family(self,family,split):self.selected=(family,split)
        def reset(self):
            assert not self.curriculum_training,'Training64slot allocation would reject num_envs=1'
            assert self.selected==('Swing','holdout')
    env=Env();spec={'recovery':{'active_family':'R0','preview_family':'Swing','sampling':{'environment_counts':{'Swing':26,'DrawBack':25,'R0':13}}}}
    assert configure_recovery_preview(env,spec)=='Swing';env.reset()
    assert spec['recovery']['sampling']['environment_counts']['Swing']==26
