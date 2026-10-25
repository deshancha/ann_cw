#ifndef GST_CALLBACK_H
#define GST_CALLBACK_H

#include <gst/video/video.h>
#include <string>
#include "Defs.h"

namespace AvatarIniOS
{
    namespace core {
    
        class IGSTCallback {
           public:
                virtual void hasMessage(TAG &tag, gchar *message)= 0;
        };


        class IGSTDataCallback : public IGSTCallback{
           public:
                virtual void hasData(TAG &tag, GstVideoInfo &videoInfo, GstMapInfo &mapInfo) = 0;
        };
    }
}

#endif
