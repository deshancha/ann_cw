#ifndef GSPIPELINE_BUILDER_H
#define GSPIPELINE_BUILDER_H

#include <gst/gst.h>
#include <gst/app/gstappsink.h>
#include <gst/video/video.h>
#include "Defs.h"
#include <map>

// Has Builder Design Pattern

namespace AvatarIniOS
{
    namespace core {

        typedef std::map<std::string, float> FloatUnifromMap;

        class IGSTCallback;
        class GSPipeline;
    
        class GSPipelineBuilder
        {
            
            GSPipeline* pipeLine;
            GSPipeline* mBasePipeLine;

            public:
                GSPipelineBuilder(IGSTCallback* callback, GMainContext *context, const char * pipeLineString,TAG &tag);

                GSPipelineBuilder(GSPipeline* existingPipeline);
            
                operator GSPipeline*() const { return std::move(pipeLine); }

                GSPipeline* getPipeLine() { return pipeLine;}

                GSPipeline* getBasePipeLine() { return mBasePipeLine;}

                // Additional Builders
                GSPipelineBuilder& appSink();
                GSPipelineBuilder& glShader(const char* fragShader, const char* vertShader);
                GSPipelineBuilder& glShader(const char* fragShader, const char* vertShader, const FloatUnifromMap &map);
                GSPipelineBuilder& glSink(guintptr renderViewId);
                GSPipelineBuilder& crop(int left, int right, int top, int bottom);

            // Fake decorator for testing
            GSPipelineBuilder& fake();
        };
    }
}
#endif
