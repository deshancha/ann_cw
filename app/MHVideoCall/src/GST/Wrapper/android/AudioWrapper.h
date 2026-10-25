#ifndef AUDIO_WRAPPER_H
#define AUDIO_WRAPPER_H

#include "IGSTCallback.h"
#include <gst/gst.h>

namespace avatarflow {
    namespace wrapper {
        namespace android {

            using namespace AvatarIniOS::core;
            class AudioWrapper {

            public:

                AudioWrapper(IGSTCallback *cb, TAG &t,
                             const char *pipeLine);

                ~AudioWrapper();

                void init();

                void play();

                void pause();

                void stop();

            private:

                TAG mTag;

                const char *mPipeLine;

                IGSTCallback *mCb;

            };
        }
    }
}

#endif
