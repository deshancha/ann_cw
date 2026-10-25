#ifndef VIDEO_WRAPPER_H
#define VIDEO_WRAPPER_H

#include "IGSTCallback.h"
#include <gst/gst.h>
#include <android/native_window.h>
#include <android/native_window_jni.h>

namespace avatarflow {
    namespace wrapper {
        namespace android {

            using namespace AvatarIniOS::core;

            class VideoWrapper {

            public:

                VideoWrapper(IGSTDataCallback *cb, TAG &t,
                             const char *pipeLine, RenderType renderType,
                             ANativeWindow *view = NULL);

                ~VideoWrapper();

                void init();

                void play();

                void pause();

                void stop();

                void setWindow(ANativeWindow *view);

                void exposeVideoOverlay();

            private:

                RenderType mRenderType;
                ANativeWindow *mUIView;;

                TAG mTag;

                const char *mPipeLine;
                IGSTDataCallback *mCb;

            };
        }
    }
}

#endif
