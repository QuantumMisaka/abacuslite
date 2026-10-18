# Troubleshooting

Start by checking the installed package and the engine command:

```bash
python -c "from importlib.metadata import version; print(version('abacuslite'))"
abacus --version
```

The first command should report the expected `abacuslite` version. The second
should print a line such as `ABACUS version v3.10.1`.

## The calculator cannot parse the ABACUS version

`Abacus` runs the configured command with `--version` when it is constructed.
If the command is a wrapper, an MPI launcher or an environment module that does
not forward `--version`, construction fails before any calculation starts.

- Use the actual executable, or a launcher that forwards arguments.
- Recent develop builds may name the binary `abacus_basic_para` instead of
  `abacus`; pass its full path.
- Check manually: `<command> --version`.

## Pseudopotential or orbital files are missing

Set `ABACUS_PP_ORB` to a directory containing the files named in the example,
or pass your own `pseudopotentials` and `basissets` mappings. ABACUS's
`tests/PP_ORB` directory is a convenient source for the examples.

`AbacusProfile` uses explicit `pseudo_dir` / `orbital_dir` first. If they are
omitted, it falls back to `ABACUS_PP_PATH` / `ABACUS_ORB_PATH`.

The SCF example needs `Si_ONCV_PBE-1.0.upf` and
`Si_gga_8au_100Ry_2s2p1d.orb`. Other examples name their own assets in the
[usage guide](usage.md).

## The solver is not available

Most examples use `ks_solver='genelpa'`, which requires an ABACUS build with
ELPA. Use a solver available in your build, for example
`ks_solver='scalapack_gvx'`; see `examples/socketio.py`.

## Socket calculation fails immediately

`AbacusSocketIO` requires an ABACUS build with the socket driver. The tested
LTS v3.10.1 build does not provide it. Use a develop build, or use the regular
`Abacus` calculator when repeated position updates are not required.

## SCF reports that no frame matches the STRU

For SCF, `abacuslite` selects the frame matching the STRU written for this run.
It checks atom order, cell components and periodic Cartesian positions, and
fails closed when no frame matches. Common causes are a changed STRU after the
calculation, an inconsistent atom mapping, or reading output from a different
calculation. Keep the input and `OUT.ABACUS` directory together.

## Native MD output is incomplete

Native MD normally reads geometry from `MD_dump` and electronic data from the
running log. Keep both files in the same `OUT.ABACUS` directory. An incomplete
`MD_dump`, or a log-only trajectory without a complete set of frames, is
rejected rather than partially parsed.

## `eig_occ.txt` is not removed

This is intentional. Output reading is read-only and repeatable; callers that
need to manage `eig_occ.txt` should do so themselves.

## MPI or OpenMP settings

Pass the launcher in `AbacusProfile.command` and set the OpenMP thread count
with `omp_num_threads` or `OMP_NUM_THREADS`. Do not put
`OMP_NUM_THREADS=...` inside the command string. The examples set one thread
for short, reproducible runs.

## Examples delete their calculation directories

Several examples remove their working directories on completion, and the
socket example clears its named directories before use. Run them in a
dedicated copy and adjust the cleanup if you need retained results.

## Metadynamics fails to start

`examples/metadynamics.py` requires a working PLUMED installation in addition
to ABACUS. See the script comments for a tested PLUMED setup.
