#ifndef GSPLAYER_H
#define GSPLAYER_H

#include <gst/gst.h>
#include <gst/app/gstappsink.h>
#include <gst/video/video.h>
#include "GSBus.h"
#include "GSMain.h"
#include "Defs.h"
#include <iostream>

#if defined(__ANDROID__)
#include <android/log.h>
#define PIPELINE_INFO(PL, MESSAGE) __android_log_print(ANDROID_LOG_INFO, "CORE_MHV", "PIPELINE:%s TYPE:%s MSG:%s", PL->getTag().c_str(), "INFO", MESSAGE);
#define PIPELINE_WARN(PL, MESSAGE) __android_log_print(ANDROID_LOG_WARN, "CORE_MHV", "PIPELINE:%s TYPE:%s MSG:%s", PL->getTag().c_str(), "WARN", MESSAGE);
#define PIPELINE_ERROR(PL, MESSAGE) __android_log_print(ANDROID_LOG_ERROR, "CORE_MHV", "PIPELINE:%s TYPE:%s MSG:%s", PL->getTag().c_str(), "ERRO", MESSAGE);
#else
#define PIPELINE_PRINT(PL, TYPE, MESSAGE) std::cout << "PIPELINE:" << PL->getTag() << " " << TYPE << ":" << MESSAGE << std::endl; //GST_DEBUG("PIPELINE:%s, %s:%s", PL->mTag.c_str(), TYPE, MESSAGE);
#define PIPELINE_INFO(PL, MESSAGE) PIPELINE_PRINT(PL, "INFO", MESSAGE);
#define PIPELINE_WARN(PL, MESSAGE) PIPELINE_PRINT(PL, "WARN", MESSAGE);
#define PIPELINE_ERROR(PL, MESSAGE) PIPELINE_PRINT(PL, "ERROR", MESSAGE);
#endif


namespace AvatarIniOS
{
    namespace core {
    
        class IGSTCallback;
        class GSPipelineBuilder;
    
        class GSPipeline
        {
        
        public:
            
            virtual ~GSPipeline();
            
            // Life cycle
            
            virtual void deInit() = 0;
            
            virtual void init() = 0;

            virtual bool start() = 0;

            virtual bool pause() = 0;

            virtual bool stop() = 0;
            
            virtual void clear() = 0;
            
            // Support
            
            virtual IGSTCallback* getCallback() = 0;
            
            virtual GstElement* getPipeLine() = 0;
            
            virtual TAG& getTag() = 0;
            
            static GSPipelineBuilder create(IGSTCallback* callback, GMainContext *context, const char * pipeLineString, TAG &tag);
        };
    }
}
#endif
