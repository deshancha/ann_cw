#ifndef GSPIPELINE_DECORATOR_GLSHADER_H
#define GSPIPELINE_DECORATOR_GLSHADER_H

#include <gst/gst.h>
#include <gst/app/gstappsink.h>
#include <gst/video/video.h>
#include "GSBus.h"
#include "GSMain.h"
#include "Defs.h"
#include <iostream>
#include "GSPipelineDecorator.h"

namespace AvatarIniOS
{
    namespace core {
    
        class GSPDecoratorGLShader : public GSPipelineDecorator
        {
            friend class GSMain;
            friend class GSPipelineBuilder;
            
        public:
            
            virtual ~GSPDecoratorGLShader();
            
            void init();
            
        protected:
            GSPDecoratorGLShader(GSPipeline *inner, const char* frag, const char* vert);
            GSPDecoratorGLShader(GSPipeline* inner, const char* frag, const char* vert, const FloatUnifromMap &map);
            
            const char* mFrag;
            const char* mVert;

            FloatUnifromMap mUniformMap;
        };
    }
}
#endif
