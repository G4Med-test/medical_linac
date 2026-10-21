#!/usr/bin/env python
"""EURADOS "Linac Action" reference data for medical_linac (GE Saturn 43, 12 MV,
10x10 cm2 field, SSD 90 cm, water phantom).

EXP_Saturn_Cal_Data.txt is an unmodified copy of
examples/advanced/medical_linac/macroAndData/experimental/EXP_Saturn_Cal_Data.txt
from Geant4 <= 11.1 (the former ML2 example; header "12 MV Eurados PTWATER").
Each line is "(x, y, z) (dx, dy, dz) dose", in mm, with the origin at the
isocentre (100 cm from the source): the water surface is at z = -100 mm, so
depth = z + 100 mm. Doses are relative to the central-axis point at 10 cm depth.

read() returns the two sets acquired with 5 mm voxels, those that match the
medical_linac scoring mesh:
- the central-axis depth-dose curve (x = y = 0, 10-240 mm depth);
- the lateral profile along y at 10 cm depth (x = 0, -110..110 mm).

Run as a script to write them as "experiment" records for the portal:
    python EuradosExp.py <output directory>
"""
import json
import os
import re
import sys

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "EXP_Saturn_Cal_Data.txt")
SURFACE_Z_MM = -100.
VOXEL_MM = 5.
PROFILE_DEPTH_MM = 100.

# Shared by the Geant4 records written by parser.py, so the portal pairs them.
BEAM_PARTICLE = "e-"
BEAM_ENERGY_MEV = 12.
TARGET = "water"
PDD = {"observableName": "percentage depth dose",
       "title": "Central-axis depth dose, 12 MV, 10x10 cm2, SSD 90 cm",
       "xAxisName": "depth in water, mm",
       "yAxisName": "dose / dose at 100 mm depth"}
PROFILE = {"observableName": "lateral dose profile",
           "title": "Lateral dose profile at 100 mm depth, 12 MV, 10x10 cm2, SSD 90 cm",
           "xAxisName": "off-axis distance (y), mm",
           "yAxisName": "dose / central-axis dose at 100 mm depth"}
PARAMETERS = [{"names": "field size", "values": "10x10 cm2"},
              {"names": "SSD", "values": "90 cm"},
              {"names": "voxel", "values": "5 mm"}]

LINE = re.compile(r"\(([^)]*)\)\s*\(([^)]*)\)\s*(\S+)\s*$")


def _points(path):
    with open(path) as f:
        for line in f:
            m = LINE.match(line.strip())
            if m:
                position = tuple(float(v) for v in m.group(1).split(","))
                size = tuple(float(v) for v in m.group(2).split(","))
                yield position, size, float(m.group(3))


def _unique(pairs, what):
    """Sort (x, dose) pairs; repeated x must carry the same dose."""
    values = {}
    for x, dose in pairs:
        if x in values and values[x] != dose:
            raise ValueError("Conflicting %s values at %g mm" % (what, x))
        values[x] = dose
    if not values:
        raise ValueError("No %s points in %s" % (what, DATA_FILE))
    return sorted(values), [values[x] for x in sorted(values)]


def read(path=DATA_FILE):
    """Return ((depths, doses), (offsets, doses)), positions in mm."""
    pdd, profile = [], []
    for (x, y, z), (dx, dy, dz), dose in _points(path):
        if (dx, dy, dz) == (VOXEL_MM, VOXEL_MM, 0.5) and x == 0 and y == 0 and dose > 0:
            pdd.append((z - SURFACE_Z_MM, dose))
        if (dx, dy, dz) == (VOXEL_MM, 0.5, VOXEL_MM) and x == 0 and z - SURFACE_Z_MM == PROFILE_DEPTH_MM:
            profile.append((y, dose))
    return _unique(pdd, "depth-dose"), _unique(profile, "profile")


def experiment_records(path=DATA_FILE):
    (depths, pdd), (offsets, profile) = read(path)
    records = []
    for meta, x, y in ((PDD, depths, pdd), (PROFILE, offsets, profile)):
        records.append({
            "article": {"inspireId": -1},
            "mctool": {"name": "experiment", "version": "experiment", "model": "experiment"},
            "testName": "experiment",
            "metadata": {"observableName": meta["observableName"],
                         "reaction": "reaction name",
                         "targetName": TARGET,
                         "beamParticle": BEAM_PARTICLE,
                         "beamEnergies": [BEAM_ENERGY_MEV],
                         "secondaryParticle": "None",
                         "parameters": PARAMETERS},
            "plotType": "SCATTER2D",
            "chart": {"nPoints": len(x), "title": meta["title"],
                      "xAxisName": meta["xAxisName"], "yAxisName": meta["yAxisName"],
                      "xValues": x, "yValues": y,
                      "xStatErrorsPlus": [], "xStatErrorsMinus": [],
                      "yStatErrorsPlus": [], "yStatErrorsMinus": [],
                      "xSysErrorsPlus": [], "xSysErrorsMinus": [],
                      "ySysErrorsPlus": [], "ySysErrorsMinus": []},
        })
    return records


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: EuradosExp.py <output directory>")
    os.makedirs(sys.argv[1], exist_ok=True)
    for name, record in zip(("eurados_pdd.json", "eurados_profile.json"), experiment_records()):
        with open(os.path.join(sys.argv[1], name), "w") as f:
            json.dump(record, f, indent=1)
