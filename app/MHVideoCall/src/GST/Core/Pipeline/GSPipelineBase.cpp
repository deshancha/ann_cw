#include "GSPipelineBase.h"
#include "IGSTCallback.h"

namespace AvatarIniOS
{
    namespace core {
        //------------------------------------------------------

        GSPipelineBase::GSPipelineBase(IGSTCallback* callback, GMainContext *context, const char* pipeLineString, TAG &tag) {
                    
            mPipeLine = NULL;
            mPipeLineBus = NULL;
            mContext = context;
            mCallback = callback;
            mPipeLineString = pipeLineString;
            mTag = tag;
                    
            gst_debug_set_threshold_for_name("Pipeline", GST_LEVEL_DEBUG);
        }
    
        //------------------------------------------------------

        GSPipelineBase::~GSPipelineBase() {
            PIPELINE_INFO(this, "Destoying");
            deInit();
        }

        //------------------------------------------------------

        void GSPipelineBase::deInit()
        {
            if(mPipeLine) {
                gst_element_set_state(mPipeLine, GST_STATE_NULL);

                gst_object_unref(mPipeLine);
                mPipeLine = nullptr;
            }
            
            delete mPipeLineBus;
            mPipeLineBus = NULL;
            mContext = NULL;
            mPipeLineString = NULL;
            mCallback = NULL;
        }

        //------------------------------------------------------

        void GSPipelineBase::init() {
            
            GError *error = NULL;
            
            PIPELINE_INFO(this, "Intitializing");
            
            if (mPipeLineString)
                mPipeLine = gst_parse_launch(mPipeLineString, &error);
            
            if (error) {
                gchar *message = g_strdup_printf("Unable to build pipeline: %s", error->message);
                g_clear_error (&error);
                mCallback->hasMessage(mTag, message);
                g_free (message);
                PIPELINE_ERROR(this, message);
                return;
            }
            
            // Creating Bus
            if (mPipeLine)
                mPipeLineBus = new GSBus(mPipeLine, mContext, this);
        }

        //------------------------------------------------------

        bool GSPipelineBase::start()
        {
            
            PIPELINE_INFO(this, "Start");
            
            if (mPipeLine) {
                isLive = (gst_element_set_state(mPipeLine, GST_STATE_PLAYING) ==
                        GST_STATE_CHANGE_NO_PREROLL);
            }

            return isLive;
        }

        //------------------------------------------------------

        bool GSPipelineBase::pause()
        {
            PIPELINE_INFO(this, "pause");
            if (mPipeLine) {
                isLive = (gst_element_set_state(mPipeLine, GST_STATE_PAUSED) ==
                          GST_STATE_CHANGE_NO_PREROLL);
            }

            return isLive;
        }

        //------------------------------------------------------

        bool GSPipelineBase::stop()
        {
            PIPELINE_INFO(this, "Stop");
            if (mPipeLine) {
                GstState state;
                gst_element_set_state(mPipeLine, GST_STATE_PAUSED);
                gst_element_get_state(mPipeLine, &state, NULL, 2 * GST_SECOND);
                gst_element_set_state(mPipeLine, GST_STATE_NULL);
                gst_element_get_state(mPipeLine, &state, NULL, 2 * GST_SECOND);
                gst_element_set_state(mPipeLine, GST_STATE_READY);
                gst_element_get_state(mPipeLine, &state, NULL, 2 * GST_SECOND);
            }

            return true;
        }

        //------------------------------------------------------

        void GSPipelineBase::clear() {
            gst_element_set_state (mPipeLine, GST_STATE_NULL);
            gst_object_unref (mPipeLine);
            mPipeLine = NULL;
        }
    }
}
