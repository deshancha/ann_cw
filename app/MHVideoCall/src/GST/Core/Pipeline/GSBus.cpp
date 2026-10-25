#include "GSBus.h"
#include "GSPipelineBase.h"
#include "IGSTCallback.h"

namespace AvatarIniOS
{
    namespace core {
    
        GSBus::GSBus(GstElement* pLine, GMainContext *ctx, GSPipelineBase* player) : pipeline(pLine), context(ctx), gsPlayer(player) {
            initBus();
        }

        //------------------------------------------------------

        GSBus::~GSBus() {
            gsPlayer = NULL;
            pipeline = NULL;
            context = NULL;
            printf("GSBus destructor--\r\n");
        }


        //------------------------------------------------------

        void GSBus::initBus() {
            GstBus *bus;
            GSource *bus_source;
            
            GST_DEBUG ("Creating Bus for Pipeline : xxx");
            
            bus = gst_element_get_bus (pipeline);
            bus_source = gst_bus_create_watch (bus);
            g_source_set_callback (bus_source, (GSourceFunc) gst_bus_async_signal_func, NULL, NULL);
            g_source_attach (bus_source, context);
            g_source_unref (bus_source);

            g_signal_connect (G_OBJECT (bus), "message::error", (GCallback)errorCallback, gsPlayer);
            g_signal_connect (G_OBJECT (bus), "message::eos", (GCallback)endOfStreamCallback, gsPlayer);
            g_signal_connect (G_OBJECT (bus), "message::state-changed", (GCallback)stateChangeCallback, gsPlayer);
            g_signal_connect (G_OBJECT (bus), "message::duration", (GCallback)durationCallback, gsPlayer);
            g_signal_connect (G_OBJECT (bus), "message::buffering", (GCallback)bufferingCallback, gsPlayer);
            g_signal_connect (G_OBJECT (bus), "message::clock-lost", (GCallback)clockLostCallback, gsPlayer);
            
            gst_object_unref (bus);
        }

        // Bus Call backs

        /* Retrieve errors from the bus and show them on the UI */
        void GSBus::errorCallback (GstBus *bus, GstMessage *msg, gpointer userData)
        {
            GSPipelineBase* gsPipeline = static_cast<GSPipelineBase*>(userData);

            GError *err;
            gchar *debug_info;
            gchar *message_string;

            gst_message_parse_error (msg, &err, &debug_info);
            message_string = g_strdup_printf ("Error received from element %s: %s", GST_OBJECT_NAME (msg->src), err->message);
            g_clear_error (&err);
            g_free (debug_info);
            gsPipeline->mCallback->hasMessage(gsPipeline->mTag, message_string);
            g_free (message_string);

            gst_element_set_state(gsPipeline->mPipeLine, GST_STATE_NULL);
        }

        //------------------------------------------------------
        /* Called when the End Of the Stream is reached. Just move to the beginning of the media and pause. */
        void GSBus::endOfStreamCallback (GstBus *bus, GstMessage *msg, gpointer userData) {
            GSPipelineBase* gsPipeline = static_cast<GSPipelineBase*>(userData);
            gsPipeline->target_state = GST_STATE_PAUSED;
            gsPipeline->isLive = (gst_element_set_state (gsPipeline->mPipeLine, GST_STATE_PAUSED) == GST_STATE_CHANGE_NO_PREROLL);
            //execute_seek (0, gsPlayer);
        }

        //------------------------------------------------------

        /* Called when buffering messages are received. We inform the UI about the current buffering level and
        * keep the pipeline paused until 100% buffering is reached. At that point, set the desired state. */
        void GSBus::bufferingCallback (GstBus *bus, GstMessage *msg, gpointer userData) {
            GSPipelineBase* gsPipeline = static_cast<GSPipelineBase*>(userData);
            gint percent;

            if (gsPipeline->isLive)
                return;

            gst_message_parse_buffering (msg, &percent);
            if (percent < 100 && gsPipeline->target_state >= GST_STATE_PAUSED) {
                gchar * message_string = g_strdup_printf ("Buffering %d%%", percent);
                gst_element_set_state (gsPipeline->mPipeLine, GST_STATE_PAUSED);
                gsPipeline->mCallback->hasMessage(gsPipeline->mTag, message_string);
                g_free (message_string);
            } else if (gsPipeline->target_state >= GST_STATE_PLAYING) {
                gst_element_set_state (gsPipeline->mPipeLine, GST_STATE_PLAYING);
            } else if (gsPipeline->target_state >= GST_STATE_PAUSED) {
                gsPipeline->mCallback->hasMessage(gsPipeline->mTag, "Buffering complete");
            }
        }

        //------------------------------------------------------

        /* Called when the duration of the media changes. Just mark it as unknown, so we re-query it in the next UI refresh. */
        void GSBus::durationCallback (GstBus *bus, GstMessage *msg, gpointer userData) {
            GSPipelineBase* gsPipeline = static_cast<GSPipelineBase*>(userData);
            
            gsPipeline->duration = GST_CLOCK_TIME_NONE;
        }

        //------------------------------------------------------

        /* Called when the clock is lost */
        void GSBus::clockLostCallback (GstBus *bus, GstMessage *msg, gpointer userData) {
            GSPipelineBase* gsPipeline = static_cast<GSPipelineBase*>(userData);
            
            if (gsPipeline->target_state >= GST_STATE_PLAYING) {
                gst_element_set_state (gsPipeline->mPipeLine, GST_STATE_PAUSED);
                gst_element_set_state (gsPipeline->mPipeLine, GST_STATE_PLAYING);
            }
        }

        //------------------------------------------------------

        /* Notify UI about pipeline state changes */
        void GSBus::stateChangeCallback (GstBus *bus, GstMessage *msg, gpointer userData) {
            GSPipelineBase* gsPipeline = static_cast<GSPipelineBase*>(userData);
            
            GstState old_state, new_state, pending_state;
            gst_message_parse_state_changed (msg, &old_state, &new_state, &pending_state);
            /* Only pay attention to messages coming from the pipeline, not its children */
            if (GST_MESSAGE_SRC (msg) == GST_OBJECT (gsPipeline->mPipeLine)) {
                gsPipeline->state = new_state;
                gchar *message = g_strdup_printf("State changed to %s", gst_element_state_get_name(new_state));
                gsPipeline->mCallback->hasMessage(gsPipeline->mTag, message);
                
                g_free (message);

                if (old_state == GST_STATE_READY && new_state == GST_STATE_PAUSED)
                {
                    //check_media_size(self);

                    /* If there was a scheduled seek, perform it now that we have moved to the Paused state */
                    //if (GST_CLOCK_TIME_IS_VALID (gsPlayer->desired_position))
                    //    execute_seek (gsPlayer->desired_position, gsPlayer);
                }
            }
        }
    }
}
