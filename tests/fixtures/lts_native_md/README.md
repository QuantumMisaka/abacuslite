# Real ABACUS LTS native-MD output

Copied without editing from the successful ABACUS v3.10.1 engine run at
`/home/james/scratch/abacuslite-current-branches-20261017/harness/LTS_generated_velocity_probe/abacus_ase_native_md_vkatv8te/OUT.ABACUS/`.
The run used `md_nstep 2`, `init_vel 0`, and `md_seed 1729`. The engine wrote
three MD steps; the pre-fix independent plugin reader failed with
`Inconsistent length: 1 != 3` because the log contains only one structure.

Retained raw files: `running_md.log` (SHA256
`680cf3a679fca6b4a83c3d23fe2418a3c07625e5fffcc47618c1aa5853c0059d`)
and `MD_dump` (SHA256
`b0b07d58f3bd873a79f563cfde4775c47c9f300cd9602e5c05732c920e9f0e67`).
The dump supplies Cartesian positions, lattice vectors in alat units, and
forces. The regression checks literal energies from the log and geometry/force
values from the dump without invoking an engine.
