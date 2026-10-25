#include "GSPipelineBuilder.h"
#include "GSPipeline.h"
#include "GSPipelineBase.h"
#include "GSPDecoratorAppsink.h"
#include "GSPDecoratorGLShader.h"
#include "GSPDecoratorGLSink.h"
#include "GSPDecoratorCrop.h"
#include "GSPDecoratorFake.h"

namespace AvatarIniOS
{
    namespace core {
        //------------------------------------------------------
    
        GSPipelineBuilder::GSPipelineBuilder(IGSTCallback* callback, GMainContext *context, const char * pipeLineString, TAG &tag) {
            GSPipelineBase* basePipeLine = new GSPipelineBase(callback, context, pipeLineString, tag);

            mBasePipeLine = basePipeLine;
            pipeLine = basePipeLine;
        }

        //------------------------------------------------------

        GSPipelineBuilder::GSPipelineBuilder(GSPipeline* existingPipeline) {
            pipeLine = existingPipeline;
        }
    
        //------------------------------------------------------

        GSPipelineBuilder&  GSPipelineBuilder::appSink() {
            pipeLine = new GSPDecoratorAppsink(pipeLine);
            
            return *this;
        }
    
        //------------------------------------------------------

        GSPipelineBuilder&  GSPipelineBuilder::glShader(const char* fragShader, const char* vertShader) {
            pipeLine = new GSPDecoratorGLShader(pipeLine, fragShader, vertShader);
            
            return *this;
        }

        //------------------------------------------------------

        GSPipelineBuilder& GSPipelineBuilder::glShader(const char* fragShader,
                                                       const char* vertShader, const FloatUnifromMap &map) {
            pipeLine = new GSPDecoratorGLShader(pipeLine, fragShader, vertShader, map);

            return *this;
        }

        //------------------------------------------------------
    
        GSPipelineBuilder&  GSPipelineBuilder::glSink(guintptr renderViewId) {
            pipeLine = new GSPDecoratorGLSink(pipeLine, renderViewId);
            
            return *this;
        }

        //------------------------------------------------------

        GSPipelineBuilder& GSPipelineBuilder::crop(int left, int right, int top, int bottom) {
            pipeLine = new GSPDecoratorCrop(pipeLine, left, right, top, bottom);

            return *this;
        }

        //------------------------------------------------------

        GSPipelineBuilder& GSPipelineBuilder::fake() {
            pipeLine = new GSPDecoratorFake(pipeLine);

            return *this;
        }
    }
}
