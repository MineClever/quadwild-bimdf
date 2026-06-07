/***************************************************************************/
/* Copyright(C) 2021


The authors of

Reliable Feature-Line Driven Quad-Remeshing
Siggraph 2021


 All rights reserved.
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
****************************************************************************/

#include <QApplication>
#include <QDesktopWidget>
#include <GL/glew.h>
#include "glwidget.h"
#include <wrap/qt/anttweakbarMapper.h>
#include <QWindow>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QTextStream>
//#include <triangle_mesh_type.h>
//#include <wrap/io_trimesh/import_field.h>
//#include <wrap/io_trimesh/import.h>

#include<vcg/complex/algorithms/hole.h>
#include <cstdio>
#include <clocale>
#include <fstream>
#include <nlohmann/json.hpp>
//#include <locale>


extern bool do_batch;
extern bool has_features;
extern bool has_features_fl;
extern std::string pathM,pathS;

extern bool do_remesh;
extern int remesher_iterations;
extern double remesher_aspect_ratio;
extern double alpha;
extern int remesher_termination_delta;

extern double sharp_feature_thr;
extern int feature_erode_dilate;

void correctOrAbort(const bool ok, const std::string & line, const int linenumber)
{
    if(!ok)
    {
        std::cerr << "[fieldComputation] Malformerd config file |-> " << line << " (" << linenumber << ")" << std::endl;
        std::cerr << "[fieldComputation] ...aborting..." << std::endl;
        abort();
    }
}

//bool loadConfigFile(const std::string & filename)
//{
//	QFile configFile(filename.c_str());

//	if (!configFile.open(QIODevice::ReadOnly))
//	{
//		//handleme
//	}

//	QTextStream configStream(&configFile);

//	int i = 0;
//    QString line;

//    while (configStream.readLineInto(&line))//(configStream.readLineInto(&line))
//	{
//		QStringList keyValuePair = line.split(' ');

//		if (keyValuePair.size() != 2)
//		{
//            correctOrAbort(false, line.toStdString(), i);
//		}

//		bool ok = false;
//		if (keyValuePair[0] == "remesh_iterations")
//		{
//			remesher_iterations = keyValuePair[1].toInt(&ok);
//            correctOrAbort(ok, line.toStdString(), i);
//			continue;
//		}
//		if (keyValuePair[0] == "remesh_target_aspect_ratio")
//		{
//			remesher_aspect_ratio = keyValuePair[1].toDouble(&ok);
//            correctOrAbort(ok, line.toStdString(), i);
//			continue;
//		}
//		if (keyValuePair[0] == "remesh_termination_delta")
//		{
//			remesher_termination_delta = keyValuePair[1].toInt(&ok);
//            correctOrAbort(ok, line.toStdString(), i);
//			continue;
//		}
//		if (keyValuePair[0] == "sharp_feature_thr")
//		{
//			sharp_feature_thr = keyValuePair[1].toDouble(&ok);
//            correctOrAbort(ok, line.toStdString(), i);
//			continue;
//		}
//		if (keyValuePair[0] == "sharp_feature_erode_dilate")
//		{
//			feature_erode_dilate = keyValuePair[1].toInt(&ok);
//            correctOrAbort(ok, line.toStdString(), i);
//			continue;
//		}

//		++i;
//	}

//	std::cout << "[fieldComputation] Successful config import" << std::endl;

//}

bool loadConfigFile(const std::string & filename)
{
    std::ifstream stream(filename.c_str());
    if (!stream.is_open()) {
        return false;
    }
    nlohmann::json json;
    stream >> json;

    std::cout<<"READ CONFIG FILE"<<std::endl;

    if (json.contains("do_remesh")) {
        if (json["do_remesh"].is_boolean()) {
            do_remesh = json["do_remesh"].get<bool>();
        } else {
            do_remesh = json["do_remesh"].get<int>() != 0;
        }
    }
    std::cout<<"do_remesh "<<do_remesh<<std::endl;

    if (json.contains("remesh_iterations")) {
        remesher_iterations = json["remesh_iterations"].get<int>();
    }
    std::cout<<"remesh_iterations "<<remesher_iterations<<std::endl;

    if (json.contains("remesh_target_aspect_ratio")) {
        remesher_aspect_ratio = json["remesh_target_aspect_ratio"].get<double>();
    }
    std::cout<<"remesher_aspect_ratio "<<remesher_aspect_ratio<<std::endl;

    if (json.contains("remesh_termination_delta")) {
        remesher_termination_delta = json["remesh_termination_delta"].get<int>();
    }
    std::cout<<"remesh_termination_delta "<<remesher_termination_delta<<std::endl;

    if (json.contains("sharp_feature_thr")) {
        sharp_feature_thr = json["sharp_feature_thr"].get<double>();
    }
    std::cout<<"sharp_feature_thr "<<sharp_feature_thr<<std::endl;

    if (json.contains("sharp_feature_erode_dilate")) {
        feature_erode_dilate = json["sharp_feature_erode_dilate"].get<int>();
    }
    std::cout<<"sharp_feature_erode_dilate "<<feature_erode_dilate<<std::endl;

    if (json.contains("alpha")) {
        alpha = json["alpha"].get<double>();
    }
    std::cout<<"alpha "<<alpha<<std::endl;

    std::cout << "[fieldComputation] Successful config import" << std::endl;

    return true;

}

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);

    //Use "." as decimal separator
    std::setlocale(LC_NUMERIC, "en_US.UTF-8");

    QWindow dummy;
    QString def_string = QString("GLOBAL fontscaling=%1").arg((int)dummy.devicePixelRatio());
    TwDefine(def_string.toStdString().c_str());
    printf("%s\n",qPrintable(def_string));
    fflush(stdout);

    // Set functions to handle string copy
    TwCopyCDStringToClientFunc(CopyCDStringToClient);
    TwCopyStdStringToClientFunc(CopyStdStringToClient);

    if( !TwInit(TW_OPENGL, NULL) )
    {
        fprintf(stderr, "AntTweakBar initialization failed: %s\n", TwGetLastError());
        return 1;
    }

    //load default config

    loadConfigFile("basic_setup.json");
    assert(argc>1);
    pathM=std::string(argv[1]);
    for (size_t i=2;i<argc;i++)
    {
        if(std::string(argv[i])==std::string("batch"))
        {
            do_batch=true;
            continue;
        }

        std::string pathTest=std::string(argv[i]);
        int position=pathTest.find(".sharp");
        if (position!=-1)
        {
            pathS=pathTest;
            has_features=true;
            continue;
        }
        position=pathTest.find(".fl");
        if (position!=-1)
        {
            pathS=pathTest;
            has_features_fl=true;
            continue;
        }
        position=pathTest.find(".json");
        if (position!=-1)
        {
           loadConfigFile(pathTest.c_str());
           continue;
        }
    }
    //    loadConfigFile("basic_setup.json");

    //    std::cout << pathM << std::endl;

    //    if ((argc>2)&&(std::string(argv[2])==std::string("batch")))
    //        do_batch=true;
    //    else
    //    {
    //        if (argc>2)
    //        {
    //            std::string pathTest=std::string(argv[2]);
    //            int position=pathTest.find(".sharp");

    //            if (position!=-1)
    //            {
    //                pathS=pathTest;
    //                has_features=true;
    //            }
    //            position=pathTest.find(".fl");
    //            if (position!=-1)
    //            {
    //                pathS=pathTest;
    //                has_features_fl=true;
    //            }
    //        }
    //    }

    //    if ((has_features || has_features_fl)&&(argc>3))
    //    {
    //        if (std::string(argv[3])==std::string("batch"))
    //            do_batch=true;
    //    }
    GLWidget window;

    window.show();
    return app.exec();
}
