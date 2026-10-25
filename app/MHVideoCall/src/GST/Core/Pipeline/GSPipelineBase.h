#ifndef GSPIPELINE_BASE_H
#define GSPIPELINE_BASE_H

#include <gst/gst.h>
#include <gst/app/gstappsink.h>
#include <gst/video/video.h>
#include "GSBus.h"
#include "GSMain.h"
#include "Defs.h"
#include <iostream>
#include "GSPipeline.h"

namespace AvatarIniOS
{
    namespace core {
    
        class GSPipelineBase : public GSPipeline
        {
            friend class GSBus;
            friend class GSMain;
            friend class GSPipelineBuilder;
            
        public:
            
            ~GSPipelineBase();
            
            void deInit();
            
            void init();

            bool start();

            bool pause();

            bool stop();
            
            void clear();
            
            IGSTCallback* getCallback() {
                return mCallback;
            }
            
            GstElement* getPipeLine() {
                return mPipeLine;
            }
            
            TAG& getTag() {
                return mTag;
            }
            
          
        protected:
        
            TAG mTag;
            IGSTCallback* mCallback;
            // GStreamer related
            GstElement* mPipeLine;
            GSBus* mPipeLineBus;
            GMainContext* mContext;       /* GLib context used to run the main loop */
            gboolean isLive;
            GstState state;
            GstState target_state;
            gint64 duration;
            
            const char* mPipeLineString;
            
        protected:
            GSPipelineBase(IGSTCallback* callback,
                GMainContext *context,
                const char * pipeLineString,
                TAG &tag);
        };
    }
}
#endif
