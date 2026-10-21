# Portal JSON parser

New parser (no `geant-config-generator` precedent: its
`tests/geant4/medical_linac/` has only `params.conf`/`template.conf`).
It compares the GE Saturn 43 linac (12 MV photon mode, 10×10 cm² field,
SSD 90 cm) with the EURADOS "Linac Action" dosimetric data (B. Caccia et al.,
EURADOS Report 2020-05).

## Run

`macro/eurados_12MV_opt4.mac` follows the original `template.conf`
(`standard_opt4`, 12 MeV electrons with σ = 0.127 MeV, 5 mm dose mesh), but it
is self-contained: it sets the gun after `/run/initialize`, because
`ActionInitialization` creates the generator and its messenger in the worker
threads. It also fixes the seeds and writes `dDep.txt` in the run directory.
`metadata()` rejects macros that change the mesh or the geometry
(`/DetectorConstruction/...`): the reference data hold only for the default
set-up.

A 5 mm voxel on the axis receives about one energy deposit per 10⁶ primary
electrons. That is why `template.conf` asked for 5·10¹⁰ events. The macro runs
10⁹ events, about 1.5 h on 8–10 threads of a recent CPU (1.9·10⁵ events/s
measured with Geant4 11.3.2 on 10 threads). With 10⁸ events the uncertainty
was 6.7% per depth-dose point and 10–13% per in-field profile point. 10⁹
events give about 2% and 3.5%; more events reduce this further, within the
6 h job limit. To get there with this many events:

- the depth dose averages the central 3×3 voxels (|x|, |y| ≤ 5 mm). The measured
  profile is flat to 0.3% there;
- the profile at 100 mm depth averages the voxels at x = −5, 0, 5 mm.

Both curves are divided by the 3×3 average at 100 mm depth, like the reference
data (1 on the axis at 10 cm depth). Errors per voxel come from the per-event
sums the scorer writes (`σ² = Σd² − (Σd)²/N`, N = `beamOn`). Covariances
between neighbouring voxels are neglected. The uncertainty of the
normalization point is a common scale factor: it is reported as the
`normalization uncertainty` parameter and not added to each point.

## Output

Two `SCATTER2D` records, `percentage depth dose` (depth 5–255 mm) and
`lateral dose profile` (−125…125 mm at 100 mm depth), with target `water`,
beam `e-` at 12 MeV and parameters `field size`, `SSD`, `voxel`, `events`
and `normalization uncertainty`.

## Known limitation: dose outside the field

`SteppingAction` kills every track that enters a jaw, travels backwards, or
leaves the target, primary collimator or flattening filter outside the
flattening-filter cone. This is a variance-reduction choice of the
application. It removes jaw transmission and most head scatter, so the
simulated dose beyond the field edge (|y| > 50 mm) is expected to be
well below the measurement. A 10⁸-event check with Geant4 11.3.2 found
30–100% less dose there. Inside the field, most points agreed with the
data within 1–2σ of that run. The exceptions were the build-up region
(15–35 mm, 10–19% low, up to 3.8σ) and the penumbra at +50 mm. These need
a check with 10⁹ events.

## Reference data

`EXP_Saturn_Cal_Data.txt` is an unmodified copy of
`examples/advanced/medical_linac/macroAndData/experimental/EXP_Saturn_Cal_Data.txt`
from Geant4 ≤ 11.1 (the former ML2 example; MD5
`2649145411e194c3ee6d890bcba257ad`). Its coordinates are relative to the
isocentre (water surface at z = −100 mm). `EuradosExp.py` reads the two 5 mm
sets: depth dose 10–240 mm and y profile at 10 cm depth. Run as a script, it
writes them as `experiment` records with the same metadata as the Geant4
records, ready to load into the portal once:

    python validation/EuradosExp.py <output directory>

## Geometry fix

`src/DetectorConstruction.cc` includes the upstream Geant4 fix
`ee0b124ab43` (medical_linac-V11-02-00, April 2024). Without it, the
primary-collimator cone is half as long as it should be, which leaves
collimator material on the beam axis, and the target production cut is 1 cm
instead of 1 mm. The copy in `geant-validation-tests` predates the fix.

## Local check

    python ../ci-workflows/validation/export.py export --repo . \
        --macro eurados_12MV_opt4.mac --input <run dir> --output <new dir> --version 11.3.2
