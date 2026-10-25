#include "GSPipeline.h"
#include "GSPipelineBuilder.h"

namespace AvatarIniOS
{
    namespace core {
        //------------------------------------------------------
    
        GSPipeline::~GSPipeline() {};
    
        GSPipelineBuilder GSPipeline::create(IGSTCallback* callback, GMainContext *context, const char * pipeLineString, TAG &tag) {
            return GSPipelineBuilder{callback, context, pipeLineString, tag};
        }
        
    }
}
