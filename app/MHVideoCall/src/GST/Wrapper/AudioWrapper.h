#ifndef AUDIO_WRAPPER_H
#define AUDIO_WRAPPER_H

#import "PWrapperDelegate.h"
#include "IGSTCallback.h"
#include <gst/gst.h>

namespace AvatarIniOS
{
    namespace wrapper {
        class AudioWrapper : core::IGSTCallback
        {
            
        public:
            
            AudioWrapper(id <PAudioWrapperDelegate> delegate, TAG& t, NSString* pipeLine);

            ~AudioWrapper();

            // IGSTCallback
            void hasMessage(TAG &tag, gchar *message);
            
            void init();
            
            void play();
            
            void stop();
            
        private:

            id <PAudioWrapperDelegate> delegate;
            
            TAG mTag;
            
            NSString* mPipeLine;
            
        };
    }
}

#endif
