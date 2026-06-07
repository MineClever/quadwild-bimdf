#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include <triangle_mesh_type.h>
#include <mesh_manager.h>
#include <vcg/space/box3.h>
#include <tracing/mesh_type.h>

#include <load_save.h>
#include <mesh_types.h>
#include <smooth_mesh.h>
#include <quad_from_patches.h>
#include <quad_mesh_tracer.h>

struct Parameters {
    Parameters() :
        remesh(true),
        sharpAngle(35),
        scaleFact(1),
        fixedChartClusters(0),
        hasFeature(false),
        hasField(false)
    {
        quadrangulationParameters.alpha = 0.02;
        quadrangulationParameters.ilpMethod = QuadRetopology::ILPMethod::LEASTSQUARES;
        quadrangulationParameters.timeLimit = 200;
        quadrangulationParameters.gapLimit = 0.0;
        quadrangulationParameters.callbackTimeLimit = {3.0, 5.0, 10.0, 20.0, 30.0, 60.0, 90.0, 120.0};
        quadrangulationParameters.callbackGapLimit = {0.005, 0.02, 0.05, 0.1, 0.15, 0.20, 0.25, 0.3};
        quadrangulationParameters.minimumGap = 0.4;
        quadrangulationParameters.isometry = true;
        quadrangulationParameters.regularityQuadrilaterals = true;
        quadrangulationParameters.regularityNonQuadrilaterals = true;
        quadrangulationParameters.regularityNonQuadrilateralsWeight = 0.9;
        quadrangulationParameters.alignSingularities = true;
        quadrangulationParameters.alignSingularitiesWeight = 0.1;
        quadrangulationParameters.repeatLosingConstraintsIterations = true;
        quadrangulationParameters.repeatLosingConstraintsQuads = false;
        quadrangulationParameters.repeatLosingConstraintsNonQuads = false;
        quadrangulationParameters.repeatLosingConstraintsAlign = true;
        quadrangulationParameters.hardParityConstraint = true;
        quadrangulationParameters.chartSmoothingIterations = 0;
        quadrangulationParameters.quadrangulationFixedSmoothingIterations = 0;
        quadrangulationParameters.quadrangulationNonFixedSmoothingIterations = 0;
        quadrangulationParameters.feasibilityFix = false;
        quadrangulationParameters.useFlowSolver = 1;
        quadrangulationParameters.flow_config_filename = "config/main_config/flow_virtual_simple.json";
        quadrangulationParameters.satsuma_config_filename = "config/satsuma/lemon.json";
    }

    bool remesh;
    float sharpAngle;
    float scaleFact;
    int fixedChartClusters;
    QuadRetopology::Parameters quadrangulationParameters;
    bool hasFeature;
    bool hasField;
};

void remeshAndField(
        FieldTriMesh& trimesh,
        const Parameters& parameters,
        const std::string& meshFilename,
        const std::string& sharpFilename,
        const std::string& fieldFilename);

void quadrangulate(
        const std::string& path,
        TriangleMesh& trimeshToQuadrangulate,
        PolyMesh& quadmesh,
        std::vector<std::vector<size_t>>& trimeshPartitions,
        std::vector<std::vector<size_t>>& trimeshCorners,
        std::vector<std::pair<size_t,size_t>>& trimeshFeatures,
        std::vector<size_t>& trimeshFeaturesC,
        std::vector<std::vector<size_t>> quadmeshPartitions,
        std::vector<std::vector<size_t>> quadmeshCorners,
        std::vector<int> ilpResult,
        const Parameters& parameters);

typename TriangleMesh::ScalarType avgEdge(const TriangleMesh& trimesh);
bool loadConfigFile(const std::string& filename, Parameters& parameters);

#include "functions.cpp"

#endif // FUNCTIONS_H
