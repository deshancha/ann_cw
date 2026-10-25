#ifndef GSPIPELINE_DECORATOR_H
#define GSPIPELINE_DECORATOR_H

#include <gst/gst.h>
#include <gst/app/gstappsink.h>
#include <gst/video/video.h>
#include "GSBus.h"
#include "GSMain.h"
#include "Defs.h"
#include <iostream>
#include "GSPipeline.h"

// Has Decorator Design Pattern

namespace AvatarIniOS
{
    namespace core {
    
        class GSPipelineDecorator : public GSPipeline
        {
            
        public:
            
            virtual ~GSPipelineDecorator();
            
            virtual void deInit();
            
            virtual void init();

            virtual bool start();

            virtual bool pause();

            virtual bool stop();
            
            virtual void clear();
            
            IGSTCallback* getCallback() {
                return mGsPipeline->getCallback();
            }
            
            GstElement* getPipeLine() {
                return mGsPipeline->getPipeLine();
            }
            
            TAG& getTag() {
                return mGsPipeline->getTag();
            }
            
        protected:
            GSPipelineDecorator(GSPipeline *inner);
            
            GSPipeline *mGsPipeline;
        };
    }
}
#endif
