#ifndef GSPIPELINE_DECORATOR_GLSINK_H
#define GSPIPELINE_DECORATOR_GLSINK_H

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
    
        class GSPDecoratorGLSink : public GSPipelineDecorator
        {
            friend class GSMain;
            friend class GSPipelineBuilder;
            
        public:
            
            virtual ~GSPDecoratorGLSink();
            
            void init();
            
        protected:
            GSPDecoratorGLSink(GSPipeline *inner, guintptr renderViewId);
            
            guintptr mRenderViewId;
        };
    }
}
#endif
