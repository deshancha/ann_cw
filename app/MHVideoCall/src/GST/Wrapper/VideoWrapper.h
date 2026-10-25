#ifndef VIDEO_WRAPPER_H
#define VIDEO_WRAPPER_H

#import "PWrapperDelegate.h"
#include "IGSTCallback.h"
#include <gst/gst.h>

namespace AvatarIniOS
{
    namespace wrapper {
    
        class VideoWrapper : core::IGSTDataCallback
        {
            
        public:
            
            VideoWrapper(id <PVideoWrapperDelegate> delegate, TAG& t, NSString* pipeLine, RenderType renderType, UIView* view = NULL);

            ~VideoWrapper();

            // IAppsinkCallback
            void hasData(TAG &tag, GstVideoInfo &videoInfo, GstMapInfo &mapInfo);
            void hasMessage(TAG &tag, gchar *message);
            
            void init();
            
            void play();
            
            void stop();
            
        private:

            id <PVideoWrapperDelegate> delegate;
            
            RenderType mRenderType;
            UIView* mUIView;;
            
            TAG mTag;
            
            NSString* mPipeLine;
            
        };
    }
}

#endif
