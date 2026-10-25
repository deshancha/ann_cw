#ifndef IDATACONVERT_H
#define IDATACONVERT_H

#include <gst/video/video.h>
#include "Defs.h"
#import "PDataConversionDelegate.h"

namespace AvatarIniOS
{
    namespace wrapper {
    
        class IDataConvert {
           public:
                virtual void dataConvert(TAG &tag, GstVideoInfo &videoInfo, GstMapInfo &mapInfo, id <PDataConversionDelegate> delegate) = 0;
            
                virtual ~IDataConvert() {};
            
        };
    }
}

#endif
