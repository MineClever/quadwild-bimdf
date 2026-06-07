#include "functions.h"
#include "trace.h"

#include <fstream>
#include <nlohmann/json.hpp>

namespace {

using Json = nlohmann::json;

bool json_bool(const Json& value)
{
    if (value.is_boolean()) {
        return value.get<bool>();
    }
    if (value.is_number_integer() || value.is_number_unsigned()) {
        return value.get<int>() != 0;
    }
    if (value.is_number_float()) {
        return value.get<double>() != 0.0;
    }
    throw std::runtime_error("expected boolean-compatible JSON value");
}

std::vector<float> json_float_array(const Json& array)
{
    if (!array.is_array()) {
        throw std::runtime_error("expected JSON array");
    }
    std::vector<float> result;
    result.reserve(array.size());
    for (size_t i = 0; i < array.size(); ++i) {
        result.push_back(array.at(i).get<float>());
    }
    return result;
}

template <typename T>
void assign_if_present(const Json& json, const char* key, T& target)
{
    if (json.contains(key)) {
        target = json.at(key).get<T>();
    }
}

void assign_bool_if_present(const Json& json, const char* key, bool& target)
{
    if (json.contains(key)) {
        target = json_bool(json.at(key));
    }
}

Json load_json_file(const std::string& filename)
{
    std::ifstream file(filename.c_str());
    if (!file.is_open()) {
        throw std::runtime_error(std::string("Failed to open config file ") + filename);
    }

    Json json;
    file >> json;
    if (!json.is_object()) {
        throw std::runtime_error(std::string("Config root must be a JSON object: ") + filename);
    }
    return json;
}

}

inline void remeshAndField(
        FieldTriMesh& trimesh,
        const Parameters& parameters,
        const std::string& meshFilename,
        const std::string& sharpFilename,
        const std::string& fieldFilename)
{
    typename MeshPrepocess<FieldTriMesh>::BatchParam BPar;
    BPar.DoRemesh=parameters.remesh;
    BPar.feature_erode_dilate=4;
    BPar.remesher_aspect_ratio=0.35; // from field_computation/basic_setup*.txt
    BPar.remesher_iterations=15;
    BPar.remesher_termination_delta=10000;
    BPar.SharpFactor=6;
    BPar.sharp_feature_thr=parameters.sharpAngle;
    BPar.surf_dist_check=true;
    BPar.UpdateSharp=(!parameters.hasFeature);

    typename vcg::tri::FieldSmoother<FieldTriMesh>::SmoothParam FieldParam;
    FieldParam.alpha_curv=0.3;
    FieldParam.curv_thr=0.8;

    if (parameters.hasFeature) {
        bool loaded=trimesh.LoadSharpFeatures(sharpFilename);
        if (!loaded)
        {
            std::cout<<"ERROR: Wrong Sharp Feature File"<<std::endl;
            exit(0);
        }
        std::cout<<"Sharp Feature Length:"<<trimesh.SharpLenght()<<std::endl;
    }
    if (!parameters.hasField) {
        MeshPrepocess<FieldTriMesh>::BatchProcess(trimesh,BPar,FieldParam);
    }
    else {
        bool success = trimesh.LoadField(fieldFilename.c_str());
        if (!success) {
            throw std::runtime_error(std::string("failed to load field  from '") + fieldFilename + "'");
        }
    }

    MeshPrepocess<FieldTriMesh>::SaveAllData(trimesh,meshFilename);
}


inline void quadrangulate(
        const std::string& filename,
        TriangleMesh& trimeshToQuadrangulate,
        PolyMesh& quadmesh,
        std::vector<std::vector<size_t>>& trimeshPartitions,
        std::vector<std::vector<size_t>>& trimeshCorners,
        std::vector<std::pair<size_t,size_t>>& trimeshFeatures,
        std::vector<size_t>& trimeshFeaturesC,
        std::vector<std::vector<size_t>> quadmeshPartitions,
        std::vector<std::vector<size_t>> quadmeshCorners,
        std::vector<int> ilpResult,
        const Parameters& parameters)
{
    //Get base filename
    std::string baseFilename=filename;
    baseFilename.erase(baseFilename.find_last_of("."));

    std::string meshFilename=baseFilename;
    meshFilename.append("_p0.obj");

    int mask;
    vcg::tri::io::ImporterOBJ<TriangleMesh>::LoadMask(meshFilename.c_str(), mask);
    int err = vcg::tri::io::ImporterOBJ<TriangleMesh>::Open(trimeshToQuadrangulate, meshFilename.c_str(), mask);
    if ((err!=0)&&(err!=5)) {
        throw std::runtime_error("error importing obj file " + meshFilename);
    }

    //FACE PARTITIONS
    std::string partitionFilename = baseFilename;
    partitionFilename.append("_p0.patch");
    trimeshPartitions = loadPatches(partitionFilename);
    std::cout<<"Loaded "<<trimeshPartitions.size()<<" patches"<<std::endl;

    //PATCH CORNERS
    std::string cornerFilename = baseFilename;
    cornerFilename.append("_p0.corners");
    trimeshCorners = loadCorners(cornerFilename);
    std::cout<<"Loaded "<<trimeshCorners.size()<<" corners set"<<std::endl;

    //FEATURES
    std::string featureFilename = baseFilename;
    featureFilename.append("_p0.feature");
    trimeshFeatures = LoadFeatures(featureFilename);
    std::cout<<"Loaded "<<trimeshFeatures.size()<<" features"<<std::endl;

    //FEATURE CORNERS
    std::string featureCFilename = baseFilename;
    featureCFilename.append("_p0.c_feature");
    trimeshFeaturesC = loadFeatureCorners(featureCFilename);
    std::cout<<"Loaded "<<trimeshFeaturesC.size()<<" corner features"<<std::endl;
    loadFeatureCorners(featureCFilename);

    std::cout<<"Alpha: "<<parameters.quadrangulationParameters.alpha<<std::endl;

    OrientIfNeeded(trimeshToQuadrangulate,trimeshPartitions,trimeshCorners,trimeshFeatures,trimeshFeaturesC);

    //COMPUTE QUADRANGULATION
    QuadRetopology::internal::updateAllMeshAttributes(trimeshToQuadrangulate);

    QuadRetopology::Parameters qParameters = parameters.quadrangulationParameters;
    const float scaleFactor = parameters.scaleFact;
    const int fixedChartClusters = parameters.fixedChartClusters;

    double edgeSize=avgEdge(trimeshToQuadrangulate)*scaleFactor;
    std::cout<<"Edge size: "<<edgeSize<<std::endl;
    const std::vector<double> edgeFactor(trimeshPartitions.size(), edgeSize);

    qfp::quadrangulationFromPatches(trimeshToQuadrangulate, trimeshPartitions, trimeshCorners, edgeFactor, qParameters, fixedChartClusters, quadmesh, quadmeshPartitions, quadmeshCorners, ilpResult);

    //SAVE OUTPUT
    std::string outputFilename = baseFilename;
    outputFilename+=std::string("_quadrangulation")+std::string(".obj");
    vcg::tri::io::ExporterOBJ<PolyMesh>::Save(quadmesh, outputFilename.c_str(),0);


    //SMOOTH
    std::vector<size_t> QuadPart(quadmesh.face.size(),0);
    for (size_t i=0;i<quadmeshPartitions.size();i++)
        for (size_t j=0;j<quadmeshPartitions[i].size();j++)
            QuadPart[quadmeshPartitions[i][j]]=i;

    std::vector<size_t> TriPart(trimeshToQuadrangulate.face.size(),0);
    for (size_t i=0;i<trimeshPartitions.size();i++)
        for (size_t j=0;j<trimeshPartitions[i].size();j++)
            TriPart[trimeshPartitions[i][j]]=i;

    std::vector<size_t> QuadCornersVect;
    for (size_t i=0;i<quadmeshCorners.size();i++)
        for (size_t j=0;j<quadmeshCorners[i].size();j++)
            QuadCornersVect.push_back(quadmeshCorners[i][j]);

    std::sort(QuadCornersVect.begin(),QuadCornersVect.end());
    auto last=std::unique(QuadCornersVect.begin(),QuadCornersVect.end());
    QuadCornersVect.erase(last, QuadCornersVect.end());

    std::cout<<"** SMOOTHING **"<<std::endl;
    MultiCostraintSmooth(quadmesh,trimeshToQuadrangulate,trimeshFeatures,trimeshFeaturesC,TriPart,QuadCornersVect,QuadPart,0.5,edgeSize,30,1);

    //SAVE OUTPUT
    std::string smoothOutputFilename = baseFilename;
    smoothOutputFilename+=std::string("_quadrangulation_smooth")+std::string(".obj");

    vcg::tri::io::ExporterOBJ<PolyMesh>::Save(quadmesh, smoothOutputFilename.c_str(),0);
}

inline typename TriangleMesh::ScalarType avgEdge(const TriangleMesh& trimesh)
{
    typedef typename TriangleMesh::ScalarType ScalarType;

    ScalarType avg=0;
    size_t num=0;

    for (size_t i=0;i<trimesh.face.size();i++) {
        for (int j=0;j<trimesh.face[i].VN();j++) {
            avg+=(trimesh.face[i].cP0(j)-trimesh.face[i].cP1(j)).Norm();
            num++;
        }
    }

    return avg/num;
}

inline bool loadConfigFile(const std::string& filename, Parameters& parameters)
{
    std::cout<<"READ CONFIG FILE"<<std::endl;
    const Json json = load_json_file(filename);

    assign_bool_if_present(json, "do_remesh", parameters.remesh);
    assign_if_present(json, "sharp_feature_thr", parameters.sharpAngle);
    assign_if_present(json, "alpha", parameters.quadrangulationParameters.alpha);
    assign_if_present(json, "scaleFact", parameters.scaleFact);
    assign_if_present(json, "fixedChartClusters", parameters.fixedChartClusters);

    if (json.contains("ilpMethod")) {
        const int value = json.at("ilpMethod").get<int>();
        parameters.quadrangulationParameters.ilpMethod =
            (value == 0) ? QuadRetopology::ILPMethod::ABS : QuadRetopology::ILPMethod::LEASTSQUARES;
    }

    assign_if_present(json, "timeLimit", parameters.quadrangulationParameters.timeLimit);
    assign_if_present(json, "gapLimit", parameters.quadrangulationParameters.gapLimit);
    if (json.contains("callbackTimeLimit")) {
        parameters.quadrangulationParameters.callbackTimeLimit = json_float_array(json.at("callbackTimeLimit"));
    }
    if (json.contains("callbackGapLimit")) {
        parameters.quadrangulationParameters.callbackGapLimit = json_float_array(json.at("callbackGapLimit"));
    }
    assign_if_present(json, "minimumGap", parameters.quadrangulationParameters.minimumGap);
    assign_bool_if_present(json, "isometry", parameters.quadrangulationParameters.isometry);
    assign_bool_if_present(json, "regularityQuadrilaterals", parameters.quadrangulationParameters.regularityQuadrilaterals);
    assign_bool_if_present(json, "regularityNonQuadrilaterals", parameters.quadrangulationParameters.regularityNonQuadrilaterals);
    assign_if_present(json, "regularityNonQuadrilateralsWeight", parameters.quadrangulationParameters.regularityNonQuadrilateralsWeight);
    assign_bool_if_present(json, "alignSingularities", parameters.quadrangulationParameters.alignSingularities);
    assign_if_present(json, "alignSingularitiesWeight", parameters.quadrangulationParameters.alignSingularitiesWeight);
    assign_bool_if_present(json, "repeatLosingConstraintsIterations", parameters.quadrangulationParameters.repeatLosingConstraintsIterations);
    assign_bool_if_present(json, "repeatLosingConstraintsQuads", parameters.quadrangulationParameters.repeatLosingConstraintsQuads);
    assign_bool_if_present(json, "repeatLosingConstraintsNonQuads", parameters.quadrangulationParameters.repeatLosingConstraintsNonQuads);
    assign_bool_if_present(json, "repeatLosingConstraintsAlign", parameters.quadrangulationParameters.repeatLosingConstraintsAlign);
    assign_bool_if_present(json, "hardParityConstraint", parameters.quadrangulationParameters.hardParityConstraint);
    assign_if_present(json, "chartSmoothingIterations", parameters.quadrangulationParameters.chartSmoothingIterations);
    assign_if_present(json, "quadrangulationFixedSmoothingIterations", parameters.quadrangulationParameters.quadrangulationFixedSmoothingIterations);
    assign_if_present(json, "quadrangulationNonFixedSmoothingIterations", parameters.quadrangulationParameters.quadrangulationNonFixedSmoothingIterations);
    assign_bool_if_present(json, "feasibilityFix", parameters.quadrangulationParameters.feasibilityFix);
    assign_if_present(json, "useFlowSolver", parameters.quadrangulationParameters.useFlowSolver);
    assign_if_present(json, "flow_config_filename", parameters.quadrangulationParameters.flow_config_filename);
    assign_if_present(json, "satsuma_config_filename", parameters.quadrangulationParameters.satsuma_config_filename);

    std::cout << "Successful config import" << std::endl;
    return true;
}
