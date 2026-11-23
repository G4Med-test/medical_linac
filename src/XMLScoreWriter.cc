//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.  It is provided  under  the terms  and *
// * conditions of the Geant4 Software License,  included in the file *
// * LICENSE and available at  http://cern.ch/geant4/license .  These *
// * include a list of copyright holders.                             *
// *                                                                  *
// * Neither the authors of this software system, nor their employing *
// * institutes,nor the agencies providing financial support for this *
// * work  make  any representation or  warranty, express or implied, *
// * regarding  this  software system or assume any liability for its *
// * use.  Please see the license in the file  LICENSE  and URL above *
// * for the full disclaimer and the limitation of liability.         *
// *                                                                  *
// * This  code  implementation is the result of  the  scientific and *
// * technical work of the GEANT4 collaboration.                      *
// * By using,  copying,  modifying or  distributing the software (or *
// * any work based  on the software)  you  agree  to acknowledge its *
// * use  in  resulting  scientific  publications,  and indicate your *
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
// Code developed by
// Silvia Pozzi (1), silvia.pozzi@iss.it
// Barbara Caccia (1), barbara.caccia@iss.it
// Carlo Mancini Terracciano (2), carlo.mancini.terracciano@roma1.infn.it
// (1) Istituto Superiore di Sanita' and INFN Roma, Italy
// (2) Univ. La Sapienza and INFN Roma, Italy

#include "XMLScoreWriter.hh"

#include "G4SystemOfUnits.hh"
#include "G4VScoringMesh.hh"

#include <fstream>
#include <iomanip>

void XMLScoreWriter::DumpQuantityToFile(const G4String& psName,
                                        const G4String& fileName,
                                        const G4String& option)
{
	// anything but .xml: standard Geant4 text output
	if (!G4StrUtil::ends_with(fileName, ".xml"))
	{
		G4VScoreWriter::DumpQuantityToFile(psName, fileName, option);
		return;
	}

	if (fScoringMesh == nullptr) return;

	// retrieve the scored quantity
	auto scoreMap = fScoringMesh->GetScoreMap();
	auto itr = scoreMap.find(psName);
	if (itr == scoreMap.end())
	{
		G4cerr << "ERROR : XMLScoreWriter : Unknown quantity, \"" << psName << "\"."
		       << G4endl;
		return;
	}
	auto* score = itr->second->GetMap();

	std::ofstream ofile(fileName);
	if (!ofile)
	{
		G4cerr << "ERROR : XMLScoreWriter : File open error -> " << fileName << G4endl;
		return;
	}

	const G4String unit      = fScoringMesh->GetPSUnit(psName);
	const G4double unitValue = fScoringMesh->GetPSUnitValue(psName);
	const G4ThreeVector halfSize = fScoringMesh->GetSize();
	const G4ThreeVector centre   = fScoringMesh->GetTranslation();

	// header: mesh geometry
	ofile << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
	      << "<scoringMesh name=\"" << fScoringMesh->GetWorldName() << "\">\n"
	      << "  <geometry shape=\"box\" unit=\"mm\">\n"
	      << "    <halfSize x=\"" << halfSize.x()/mm << "\" y=\"" << halfSize.y()/mm
	      <<             "\" z=\"" << halfSize.z()/mm << "\"/>\n"
	      << "    <translation x=\"" << centre.x()/mm << "\" y=\"" << centre.y()/mm
	      <<                "\" z=\"" << centre.z()/mm << "\"/>\n"
	      << "    <nBins x=\"" << fNMeshSegments[0] << "\" y=\"" << fNMeshSegments[1]
	      <<          "\" z=\"" << fNMeshSegments[2] << "\"/>\n"
	      << "  </geometry>\n"
	      << "  <quantity name=\"" << psName << "\" unit=\"" << unit
	      << "\" factor=\"" << fact << "\">\n";

	// voxels: same content as the standard text dump
	// (sum of values, sum of squared values, number of entries)
	ofile << std::setprecision(16);  // full double precision, as in G4VScoreWriter
	for (G4int ix = 0; ix < fNMeshSegments[0]; ++ix)
	{
		for (G4int iy = 0; iy < fNMeshSegments[1]; ++iy)
		{
			for (G4int iz = 0; iz < fNMeshSegments[2]; ++iz)
			{
				G4double value = 0., value2 = 0.;
				G4int entries = 0;

				auto v = score->find(GetIndex(ix, iy, iz));
				if (v != score->end())
				{
					value   = v->second->sum_wx()  / unitValue * fact;
					value2  = v->second->sum_wx2() / unitValue / unitValue * fact * fact;
					entries = v->second->n();
				}

				ofile << "    <voxel ix=\"" << ix << "\" iy=\"" << iy << "\" iz=\"" << iz
				      << "\" value=\"" << value << "\" value2=\"" << value2
				      << "\" entries=\"" << entries << "\"/>\n";
			}
		}
	}

	ofile << "  </quantity>\n"
	      << "</scoringMesh>\n";
	ofile.close();
}
