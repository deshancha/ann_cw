#include "GSMain.h"
#include "IGSTCallback.h"
#include "GSPipeline.h"
#include "IGSTMainCallback.h"

GST_DEBUG_CATEGORY_STATIC (debug_category);
#define GST_CAT_DEFAULT debug_category

namespace AvatarIniOS
{
    namespace core {
        //------------------------------------------------------

        GSMain::GSMain(){
            initialized = false;
            GST_DEBUG_CATEGORY_INIT (debug_category, "AVCORE", 0, "iOS");
            gst_debug_set_threshold_for_name("AVCORE", GST_LEVEL_DEBUG);
        }

        //------------------------------------------------------

        GSMain::~GSMain() {

            clearAllPipeLines();
            
            if (mainLoop) {
                g_main_loop_quit(mainLoop);
            }
        }

        //------------------------------------------------------

        void GSMain::clearAllPipeLines(){
            for (PipeLineItr i = mPipeLines.begin(); i != mPipeLines.end(); ++i) {
                (*i).second->clear();
            }

            for (PipeLineItr i = mPipeLines.begin(); i != mPipeLines.end(); ++i) {
                delete (*i).second;
            }

            mPipeLines.clear();
            initialized = false;
        }

        //------------------------------------------------------

        void GSMain::initGStreamer() {
            
            GST_DEBUG ("Creating Context");
            
            /* Create our own GLib Main Context and make it the default one */
            mContext = g_main_context_new ();
            g_main_context_push_thread_default(mContext);
        }

        //------------------------------------------------------

        void GSMain::startMainLoop(IGSTMainCallback* cb) {
            /* Create a GLib Main Loop and set it to run */
            GST_DEBUG ("Entering main loop...");
            mainLoop = g_main_loop_new (mContext, FALSE);
            
            if (!initialized && mainLoop) {
                GST_DEBUG ("Initialization complete, notifying application.");
                cb->gstInitialized();
                initialized = TRUE;
            }
            
            g_main_loop_run (mainLoop);
            GST_DEBUG ("Exited main loop");
            g_main_loop_unref (mainLoop);
            mainLoop = NULL;
            
            /* Free resources */
            g_main_context_pop_thread_default(mContext);
            g_main_context_unref (mContext);
            
            for( PipeLineItr i = mPipeLines.begin(); i!=mPipeLines.end(); ++i) {
                (*i).second->clear();
            }
        }

        //------------------------------------------------------

        bool GSMain::stopAllPipeLines()
        {
            for( PipeLineItr i = mPipeLines.begin(); i!=mPipeLines.end(); ++i) {
                (*i).second->stop();
            }

            return true;
        }
    
        //------------------------------------------------------
    
        GSPipeline* GSMain::createPipeLine(IGSTCallback* cb, TAG &t, const char* mPipeLineString) {
            GSPipelineBuilder builder = GSPipeline::create(cb, mContext, mPipeLineString, t);
            
            mPipeLines[t] = (GSPipeline*)builder;
            
            return builder;
        }

        //------------------------------------------------------

        GSPipeline* GSMain::createAppsinkPipeLine(IGSTCallback* cb, TAG &t, const char* mPipeLineString) {
            
            GSPipelineBuilder builder = GSPipeline::create(cb, mContext, mPipeLineString, t)
                                        .appSink();
            
            mPipeLines[t] = (GSPipeline*)builder;
            
            return builder;
        }
    
        //------------------------------------------------------
    
        GSPipeline* GSMain::createGLSinkPipeLine(IGSTCallback* cb, TAG &t, const char* mPipeLineString, guintptr mRenderViewId, const char* fragShader, const char* vertShader) {
            GSPipelineBuilder builder = GSPipeline::create(cb, mContext, mPipeLineString, t)
                                        .glSink(mRenderViewId)
                                        .glShader(fragShader, vertShader);
            
            mPipeLines[t] = builder.getBasePipeLine();
            
            return builder;
        }

        //------------------------------------------------------

        GSPipeline* GSMain::getPipeLine(TAG &t) {
            
            PipeLineItr it = mPipeLines.find(t);
            
            if(it != mPipeLines.end()) {
               return it->second;
            } else {
                return NULL;
            }
        }
    }
}
