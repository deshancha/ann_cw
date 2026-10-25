#ifndef CORE_WRAPPER_H
#define CORE_WRAPPER_H

#import <Foundation/Foundation.h>
#import "PWrapperDelegate.h"
#include "IGSTMainCallback.h"
#include <gst/gst.h>

namespace AvatarIniOS
{
    namespace wrapper {
    
        class CoreWrapper : core::IGSTMainCallback
        {
            
        public:
            
            CoreWrapper(id <PCoreWrapperDelegate> delegate);

            ~CoreWrapper();
            
            // IGSTMainCallback
            void gstInitialized();

            void initGStreamer();
            
            void startMain();
            
            void stopAllPipeLines();
            
        private:

            id <PCoreWrapperDelegate> delegate;
            
            TAG mTag;
            
        };
    }
}

#endif
