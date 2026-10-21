# medical_linac

**MV X-ray radiotherapy beam from a clinical linac** (GE Saturn 43, 12 MV
photon mode, 10×10 cm² field), validated against the EURADOS "Linac Action"
intercomparison dosimetric data. Authors: S. Pozzi, B. Caccia (with
C. Mancini Terracciano); past contributors C. Andenna, P. Cirrone,
A. Occhigrossi, S. Guatelli, M. Piergentili, M.G. Pia, F. Foppiano.

---

## 🔬 What this test does

An e- beam hits the linac target/flattening-filter assembly, producing a
megavoltage bremsstrahlung X-ray beam; the dose deposited in a water phantom
is scored on a 3-D mesh (`/score/create/boxMesh`, 5 mm voxels) and compared
to the EURADOS Linac Action reference data (B. Caccia et al., *"A model
validation scheme for Monte Carlo simulations of a medical linear
accelerator"*, EURADOS Report 2020-05).

## ⚠️ No JSON-generator script available

Unlike the other repositories in this organization,
`geant-config-generator/tests/geant4/medical_linac/` has **no `parser.py`**
(only `params.conf`/`template.conf`, no `run.sh` either) — the JSON export
for this test was never wired into the config-generator pipeline. This
import therefore only brings in the Geant4 source code; `validation/parser.py`
is left as the unmodified template placeholder (TODO) and needs to be
written from scratch, following the pattern used by the other tests'
`metadata()`/`parse()` functions.

A second, unconnected candidate exists at
`geant-validation-tests/src/g4med_elinac6MeV` (a GDML-based 6 MV linac
model by S. Guatelli, 2021) — also with no config-generator counterpart. It
was not imported here; worth a look if `medical_linac`'s own code proves
hard to adapt.

## Import notes

- `main.cc`, `include/`, `src/` come from `medical_linac.cc`/`include`/`src`
  in `geant-validation-tests/src/medical_linac`.
- `macro/` contains the two macros found directly in that source tree
  (`run.mac`, `vis.mac`).
