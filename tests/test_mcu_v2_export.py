FROZEN_TEST_SCOPE='PORTABLE'
import torch,numpy as np
from native_stand.students.model import Student
from native_stand.students.export import DeterministicActor

def test_onnx_actor_only_fixed_batch_and_numerics(tmp_path):
 import onnx
 from onnx.reference import ReferenceEvaluator
 torch.manual_seed(3);actor=Student(version='multiskill_mcu_v2');model=DeterministicActor(actor).eval();x=torch.linspace(-1,1,31)[None];path=tmp_path/'actor.onnx'
 assert not any('log_std' in k for k in model.state_dict())
 torch.onnx.export(model,x,path,input_names=['input'],output_names=['mean'],opset_version=17,dynamo=False)
 graph=onnx.load(path);onnx.checker.check_model(graph)
 assert [d.dim_value for d in graph.graph.input[0].type.tensor_type.shape.dim]==[1,31]
 assert sum(np.prod(t.dims) for t in graph.graph.initializer)==14630
 assert set(n.op_type for n in graph.graph.node)=={'Gemm','Elu','Tanh'}
 actual=ReferenceEvaluator(graph).run(None,{'input':x.numpy()})[0]
 np.testing.assert_allclose(actual,model(x).detach().numpy(),atol=1e-5,rtol=0)
