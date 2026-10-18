# From the ase-abacus fork to abacuslite

## Lineage

```text
ase-abacus (ASE fork)
  -> ABACUS interfaces/ASE_interface (historical source)
     -> QuantumMisaka/abacuslite (standalone distribution)
        -> ABACUS interfaces/ASE_interface/tests (proposed in PR #8175)
```

The calculator API is intentionally continuous. What changed is where the
ABACUS-specific code lives, how it is installed and released, and how output
formats are selected.

## What stays the same

`AbacusProfile`, `AbacusTemplate`, `Abacus` and `AbacusSocketIO` still map onto
ASE's public calculator bases: `BaseProfile`, `CalculatorTemplate`,
`GenericFileIOCalculator` and `SocketIOCalculator`. ASE still owns the
calculator lifecycle, optimization, MD and NEB algorithms:

```text
ASE property request
  -> Abacus.calculate
     -> write INPUT/STRU/KPT
     -> run ABACUS
     -> read running log / MD_dump
  -> energy, forces, stress and related results
```

## What changed from the old repository

| Area | `ase-abacus` fork | `abacuslite` |
| --- | --- | --- |
| Distribution | A fork of ASE with ABACUS files inside the ASE tree | A standalone wheel/sdist that depends on upstream ASE |
| Import path | `ase.calculators.abacus`, `ase.io.abacus` | `abacuslite`, `abacuslite.io.*` |
| ASE source | Users need the fork (or copied files) | Standard ASE; no patch or fork |
| I/O layout | One large `ase/io/abacus.py` | `generalio`, `legacyio`, `latestio`, `ksampling` |
| Output formats | One reader path tied to the fork's ABACUS version | develop `latestio` and 3.10.x LTS `legacyio`; selected per calculator |
| Version probe | Raw `abacus --version` output; not used to choose a reader | Parsed at construction; selects the reader; construction needs a working engine |
| SCF frames | Last frame from the log | Current-STRU match with atom-order, cell and periodic checks; fail-closed |
| Pseudopotentials / orbitals | Copies provided files into the run directory; `ABACUS_PP_PATH` / `ABACUS_ORBITAL_PATH` defaults | Profile directories (or `ABACUS_PP_PATH` / `ABACUS_ORB_PATH` fallback) plus explicit `pseudopotentials` / `basissets`; no implicit copy |
| Fork-only extras | `dipole`/`tddft` and `spap_analysis` | Not part of the package; use ABACUS or ASE directly |
| Validation | Tied to the ASE fork's own tests | Package, installed-consumer and two-engine CI |

## Practical consequences

- Install `ase` and `abacuslite` normally; the old fork is unnecessary.
- Change imports from `ase.calculators.abacus` to `abacuslite`; the
  calculator classes keep their names.
- Configure `AbacusProfile` with the pseudopotential/orbital directories and
  pass the file mappings to `Abacus`. The examples use `ABACUS_PP_ORB` as a
  convention; the library uses the profile directories.
- If the directory arguments are omitted, `AbacusProfile` reads only
  `ABACUS_PP_PATH` / `ABACUS_ORB_PATH`.
- Constructing `Abacus` probes `abacus --version`. Use `abacuslite.io.*`
  directly for file-only work that does not need the engine.
- For output-only work, call `legacyio.read_abacus_out` or
  `latestio.read_abacus_out` explicitly if the producing format is known.
- ABACUS supplies the engine; ATST and Forge own higher-level workflows.

See [migration](migration.md) for caller changes, [supported versions](supported-versions.md)
for tested engines, [the socket adapter contract](socket-contract.md) for the
engine/adapter boundary, and [UPSTREAM.md](../UPSTREAM.md) for source
attribution.
