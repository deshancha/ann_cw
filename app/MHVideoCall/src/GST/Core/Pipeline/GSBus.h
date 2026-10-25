
#ifndef GSBUS_H
#define GSBUS_H

#include <gst/gst.h>
#include <gst/app/gstappsink.h>
#include <gst/video/video.h>
#include <string>

namespace AvatarIniOS
{
    namespace core {
        class GSPipelineBase;

        class GSBus
        {

        public:
            GSBus(GstElement* pLine, GMainContext *ctx, GSPipelineBase* player);

            ~GSBus();
            
        private:
            GSPipelineBase* gsPlayer;
            // GStreamer related
            GstElement* pipeline;
            GMainContext *context;
            
            void initBus();
            
            // Bus callbacks
            static void errorCallback (GstBus *bus, GstMessage *msg, gpointer userData);
            static void endOfStreamCallback(GstBus *bus, GstMessage *msg, gpointer userData);
            static void bufferingCallback (GstBus *bus, GstMessage *msg, gpointer userData);
            static void clockLostCallback (GstBus *bus, GstMessage *msg, gpointer userData);
            static void stateChangeCallback (GstBus *bus, GstMessage *msg, gpointer userData);
            static void durationCallback (GstBus *bus, GstMessage *msg, gpointer userData);
           
        };
    }
}

#endif
