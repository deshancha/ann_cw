#ifndef GSPIPELINE_DECORATOR_APPSINK_H
#define GSPIPELINE_DECORATOR_APPSINK_H

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
    
        enum CBIdentifier {
            CALLBACK_IDEITIFIER_NONE,
            CALLBACK_IDEITIFIER_NEW_PREROLL, // - new_preroll
            CALLBACK_IDEITIFIER_NEW_SAMPLE   // - new_sample
        };
    
        class Async;
        class IGSTDataCallback;
        
        class GSPDecoratorAppsink : public GSPipelineDecorator
        {
            friend class GSMain;
            friend class GSPipelineBuilder;
            
        public:
            
            virtual ~GSPDecoratorAppsink();
            
            void deInit();
            
            void init();
            
        protected:
            GSPDecoratorAppsink(GSPipeline *inner);
            
        protected:
            GstAppSink* mAppSink;
            
            CBIdentifier callbackIdentifier;

            bool isDone;
            
            Async* asyncWork;
            
            IGSTDataCallback* mDataCallback;
            
        protected:
            
            // =========== Gstreamer Appsink ================
            // GstAppSinkCallbacks
            static GstFlowReturn callBackNewPreroll(GstAppSink *appsink, gpointer userData);    // new_preroll

            static GstFlowReturn callBackNewSample(GstAppSink *appsink, gpointer userData);        // new_sample

            // Handle callback receive common updates
            void handleCallbackUpdates();

            // Grab appsink data
            void startAppSinkReader();

            // handle Video Sample Buffer
            void handleVideoSample(GstSample* sample, bool display);
            
            GstVideoInfo getVideoInfo(GstSample *sample);
        };
    }
}
#endif
