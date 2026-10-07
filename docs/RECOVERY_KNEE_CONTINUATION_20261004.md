# Knee-stop Recovery continuation

Entry: root STATUS.md. New spec/ledger: configs/experiments/recovery_knee_stop_pitch_20261004.
The20-checkpoint review is historical original-USD evidence, not new-USD acceptance.
Recommended update1400 SHA00f80bbe4e29cf272c0f35abafc2b8ca33d028b1dcd65aa58cfffc160d9a7464.
Latepitch0.321rad and vx0.708m/s remain failures; no accepted Recovery candidate.

Corrected USD SHA32a56efc5ee677a7ae3b5e59c3848a141276ec4957757acde239b774b0c901b7.
Only knee extension bounds changed: left[-0.233,2.5],right[-2.5,0.233]rad.
Flattened isolated copy preserves referenced asset identities; original USD unchanged.
This is a solver mechanical stop with finite compliance, not an infinite-force guarantee.
It supplies no gas spring force. Captured pose224308 was minimally closure-resolved;
short runtime settling accepted64/64, with explicit second velocity-zero before PPO.
Neither arbitrary random poses nor3s passive settling are claimed verified here.

Reward change: pitch cost `-gate(height)*(canonical_pitch/0.2)^2*0.01`,
gate grows0→1 over0.32→0.38m. Canonical up is assetY, forward is -assetZ;
pitch=atan2(projected_gravity_Z,-projected_gravity_Y). Sign does not affect this cost.
Previous lift/upright/overshoot/settling retained. No extra force, wheel lock or compensation.
Source actor/critic/Adam strictly restored; LR3e-5 reapplied. PhysX resets fresh.
New asset and source asset identities recorded separately.

Budget3smoke+9997formal=10000actual updates,64x128,81,920,000samples maximum.
Formal wall cap explicitly null; stop on update cap, runtime fault or user signal.
No automatic restart. Per100checkpoint,per500fullevaluation plus final.
Autonomous Recovery2s hold success remains distinct from frozen-STAND takeover.

Source snapshots and original failed attempts preserved. Existing formal monitor writes
analysis, candidate selection, completion report and HAPI callback. Independent guard
reports supervisor exit before formal; it never launches PPO or changes ledger.
