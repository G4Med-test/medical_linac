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

## Validation

`geant-config-generator/tests/geant4/medical_linac/` never had a `parser.py`,
so the JSON export was written from scratch: `validation/parser.py` turns the
dose mesh of `macro/eurados_12MV_opt4.mac` into a central-axis depth-dose
curve and a lateral profile at 10 cm depth, and `validation/EuradosExp.py`
provides the EURADOS reference data. `macro/unit.mac` is the short smoke test
run on every push. Details: [validation/README.md](validation/README.md).

`src/DetectorConstruction.cc` includes the upstream Geant4 geometry fix of
April 2024 (primary-collimator cone, target production cut), missing from the
`geant-validation-tests` copy.

## Import notes

- `main.cc`, `include/`, `src/` come from `medical_linac.cc`/`include`/`src`
  in `geant-validation-tests/src/medical_linac`.
- `macro/` contains the two macros found directly in that source tree
  (`run.mac`, `vis.mac`).
- `src/DetectorConstruction.cc` then received the upstream fix `ee0b124ab43`
  (Geant4 medical_linac-V11-02-00).
