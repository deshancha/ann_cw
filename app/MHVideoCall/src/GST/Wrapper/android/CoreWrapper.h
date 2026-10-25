#ifndef CORE_WRAPPER_H
#define CORE_WRAPPER_H

#include "IGSTMainCallback.h"
#include <gst/gst.h>

namespace avatarflow {
    namespace wrapper {
        namespace android {

            using namespace AvatarIniOS::core;

            class CoreWrapper
            {

            public:

                CoreWrapper(IGSTMainCallback* cb);

                ~CoreWrapper();

                // IGSTMainCallback
                void gstInitialized();

                void initGStreamer();

                void startMain();

                void stopAllPipeLines();

            private:

                IGSTMainCallback* mCb;

            };
        }
    }
}

#endif
