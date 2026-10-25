#ifndef GSMAIN_H
#define GSMAIN_H

#include <gst/gst.h>
#include <gst/app/gstappsink.h>
#include <gst/video/video.h>
#include "Defs.h"
#include <map>
#include "GSPipelineBuilder.h"

namespace AvatarIniOS
{
    namespace core {
        class GSPipeline;
        class IGSTCallback;
        class IGSTMainCallback;

        typedef std::map<std::string, GSPipeline*> PipeLines;
        typedef std::map<std::string, GSPipeline*>::iterator PipeLineItr;

        class GSMain
        {
        public:
            
            static GSMain& getInstance()
            {
                static GSMain instance; // Guaranteed to be destroyed.
                                      // Instantiated on first use.
                return instance;
            }
            
            ~GSMain();
            
            void initGStreamer();
            
            void startMainLoop(IGSTMainCallback* cb);
            
            bool stopAllPipeLines();

            void clearAllPipeLines();
            
            GSPipeline* createPipeLine(IGSTCallback* cb, TAG &t, const char* mPipeLineString);
            
            GSPipeline* createAppsinkPipeLine(IGSTCallback* cb, TAG &t, const char* mPipeLineString);
            
            GSPipeline* createGLSinkPipeLine(IGSTCallback* cb, TAG &t, const char* mPipeLineString, guintptr mRenderViewId, const char* fragShader = 0, const char* vertShader = 0);
            
            GSPipeline* getPipeLine(TAG &t);
            
            inline bool isInitialized() {return initialized;}
            
        private:
            GSMain(GSMain const&);
            
            void operator=(GSMain const&);
            
            GSMain();
            
            GMainContext *mContext;       /* GLib context used to run the main loop */
            GMainLoop *mainLoop;
            gboolean initialized;
            
            PipeLines mPipeLines;
        };
    }
}
#endif
