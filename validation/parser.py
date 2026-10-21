#!/usr/bin/env python

# medical_linac portal parser: metadata() reads the macro, parse() the dose
# mesh written by /score/dumpQuantityToFile (GE Saturn 43, 12 MV, 10x10 cm2,
# SSD 90 cm; EURADOS "Linac Action" set-up).
#
# New parser: geant-config-generator/tests/geant4/medical_linac has only
# params.conf/template.conf, no parser.py. The mesh and normalization follow
# the EURADOS data in EXP_Saturn_Cal_Data.txt (see EuradosExp.py), so the
# records pair with the "experiment" ones that EuradosExp.py writes.
#
# Mesh: 51x51x51 voxels of 5 mm. The water surface is at z = 0 and the mesh
# starts at z = 2.5 mm, so depth bin k is centred at 5*(k+1) mm; lateral bin i
# is centred at 5*(i-25) mm.
#
# A 5 mm voxel on the axis gets ~1 energy deposit per 1e6 primary electrons, so:
# - the depth dose averages the central 3x3 voxels (|x|, |y| <= 5 mm, inside
#   the flat part of the field: the measured profile is 1 within 0.3% there);
# - the profile at 100 mm depth averages the three voxels at x = -5, 0, 5 mm.
# Both are divided by the same reference, the 3x3 average at 100 mm depth,
# like the EURADOS data (1 on the axis at 100 mm depth).
#
# Errors: per-voxel standard error from the per-event sums written by the
# scorer (sum and sum of squares over events), sigma^2 = sum2 - sum^2/N with
# N = beamOn. Covariances between neighbouring voxels are neglected; the
# relative uncertainty of the reference is reported as a parameter, not
# propagated to each point (it is a common scale factor).
import math
import os

from geantval import energy_mev, getJSON, one_command, single_run

from EuradosExp import BEAM_PARTICLE, PARAMETERS, PDD, PROFILE, TARGET

MESH = {"/score/create/boxMesh": "boxMesh_1",
        "/score/mesh/translate/xyz": "0 0 130 mm",
        "/score/mesh/boxSize": "127.5 127.5 127.5 mm",
        "/score/mesh/nBin": "51 51 51",
        "/score/quantity/doseDeposit": "dDep"}
NBIN = 51
CENTRE = 25                  # lateral bin on the beam axis
VOXEL_MM = 5.
PROFILE_DEPTH_BIN = 19       # centred at 100 mm depth
AVERAGE = (CENTRE - 1, CENTRE, CENTRE + 1)

# The validated geometry is the DetectorConstruction default (10x10 cm2 field,
# SSD 90 cm, 25.5 cm phantom): the reference data hold for that set-up only.
GEOMETRY_COMMANDS = ("/DetectorConstruction/Acc/fieldSide",
                     "/DetectorConstruction/Acc/sourceToSkinDistance",
                     "/DetectorConstruction/Phantom/phantomSide",
                     "/DetectorConstruction/Phantom/voxelSide",
                     "/DetectorConstruction/Phantom/voxelDepth")


def metadata(commands):
    events = single_run(commands)
    for command, expected in MESH.items():
        value = " ".join(one_command(commands, command).split())
        if value != expected:
            raise ValueError("Expected %s %s, got %s" % (command, expected, value))
    for command, value in commands:
        if command in GEOMETRY_COMMANDS:
            raise ValueError("The EURADOS reference holds for the default geometry: remove " + command)
    mesh, quantity, filename = one_command(commands, "/score/dumpQuantityToFile").split()
    if (mesh, quantity) != (MESH["/score/create/boxMesh"], MESH["/score/quantity/doseDeposit"]):
        raise ValueError("Dump the dose mesh: /score/dumpQuantityToFile boxMesh_1 dDep <file>")
    if os.path.isabs(filename):
        raise ValueError("Write the dose file in the run directory: " + filename)
    return {"TEST": "medical_linac",
            "PHYSLIST": one_command(commands, "/physics/addPhysics"),
            "ENERGY": energy_mev(one_command(commands, "/PrimaryGenerator/gunMeanEnergy")),
            "NEVENTS": events,
            "OUTPUT": filename}


def read_mesh(path, nevents):
    """Return {(iX, iY, iZ): (dose, sigma)} in Gy, total over the run."""
    voxels = {}
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            ix, iy, iz, total, total2, _ = line.split(",")
            total, total2 = float(total), float(total2)
            sigma = math.sqrt(max(total2 - total * total / nevents, 0.))
            voxels[int(ix), int(iy), int(iz)] = (total, sigma)
    if len(voxels) != NBIN ** 3:
        raise ValueError("Expected %d voxels in %s, found %d" % (NBIN ** 3, path, len(voxels)))
    return voxels


def average(voxels, keys):
    keys = list(keys)
    dose = sum(voxels[k][0] for k in keys) / len(keys)
    sigma = math.sqrt(sum(voxels[k][1] ** 2 for k in keys)) / len(keys)
    return dose, sigma


def parse(job):
    voxels = read_mesh(os.path.join(job["path"], job["OUTPUT"]), job["NEVENTS"])

    pdd = [average(voxels, ((i, j, k) for i in AVERAGE for j in AVERAGE)) for k in range(NBIN)]
    reference, reference_sigma = pdd[PROFILE_DEPTH_BIN]
    if reference <= 0:
        raise ValueError("No dose on the axis at 100 mm depth: too few events?")
    profile = [average(voxels, ((i, j, PROFILE_DEPTH_BIN) for i in AVERAGE)) for j in range(NBIN)]

    parameters = PARAMETERS + [
        {"names": "events", "values": str(job["NEVENTS"])},
        {"names": "normalization uncertainty", "values": "%.2g%%" % (100. * reference_sigma / reference)}]

    curves = ((PDD, [VOXEL_MM * (k + 1) for k in range(NBIN)], pdd),
              (PROFILE, [VOXEL_MM * (j - CENTRE) for j in range(NBIN)], profile))
    for meta, x, values in curves:
        y = [dose / reference for dose, _ in values]
        err = [sigma / reference for _, sigma in values]
        yield getJSON(job, "chart",
                      mctool_name="GEANT4",
                      mctool_model=job["PHYSLIST"],
                      observableName=meta["observableName"],
                      targetName=TARGET,
                      beamParticle=BEAM_PARTICLE,
                      beamEnergies=[job["ENERGY"]],
                      secondaryParticle="None",
                      title=meta["title"],
                      xAxisName=meta["xAxisName"],
                      yAxisName=meta["yAxisName"],
                      parameters=parameters,
                      xValues=x,
                      yValues=y,
                      yStatErrorsPlus=err,
                      yStatErrorsMinus=err)
