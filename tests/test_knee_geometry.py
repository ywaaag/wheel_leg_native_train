import math
import torch

from native_stand.recovery.knee_geometry import extension_guard, relative_body_angle


def test_relative_angle_matches_captured_pose():
    # Values copied from pose_0000_d9204dc9.json body_pose_w.
    upper = torch.tensor([[0.2127445489, 5.6753706e-05, 2.6170691e-04, 0.9771077633]])
    lower = torch.tensor([[0.0970674753, 2.5774305e-05, 2.6654736e-04, 0.9952777624]])
    value = float(relative_body_angle(upper, lower)[0])
    assert abs(value - 0.2343248294) < 1e-5


def test_guard_allows_reference_with_tolerance_and_rejects_extension():
    allowed, excess = extension_guard(torch.tensor([0.2339, 0.24]), 0.233, 1e-3)
    assert allowed.tolist() == [True, False]
    assert excess[0].item() == 0.0
    assert excess[1].item() > 0.0
