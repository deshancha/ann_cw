#include "VideoWrapper.h"
#include "GSMain.h"
#include <string>
#include "Defs.h"
#include "GSPipeline.h"

namespace avatarflow {
    namespace wrapper {
        namespace android {

            VideoWrapper::VideoWrapper(IGSTDataCallback *cb, TAG& t, const char* pipeLine, RenderType renderType, ANativeWindow * view) :
            mCb(cb),
            mTag(t),
            mRenderType(renderType),
            mUIView(view),
            mPipeLine(pipeLine){

                switch (renderType) {
                    case APPSINK_OPENGL:
                        break;
                    case APPSINK_CG:
                        break;
                    default:
                        break;
                }
            }

            //------------------------------------------------------

            VideoWrapper::~VideoWrapper() {
                //stop();
                mUIView = NULL;
                mCb = NULL;
            }

            //------------------------------------------------------

            void VideoWrapper::init() {
                GSPipeline* decoratedPipeline = NULL;

                if (mRenderType == APPSINK_OPENGL || mRenderType == APPSINK_CG) {
                    decoratedPipeline = GSMain::getInstance().createAppsinkPipeLine(mCb, mTag, mPipeLine);
                    decoratedPipeline->init();
                } else if (mRenderType == GLSINK && mUIView != NULL) {
                    decoratedPipeline = GSMain::getInstance().createGLSinkPipeLine(mCb, mTag, mPipeLine, (guintptr) mUIView, NULL, NULL);
                    decoratedPipeline->init();
                } else {
                    // eg: No sink video sender
                    decoratedPipeline = GSMain::getInstance().createPipeLine(mCb, mTag, mPipeLine);
                    decoratedPipeline->init();
                }

                //delete decoratedPipeline;
            }

            //------------------------------------------------------

            void VideoWrapper::play() {
                GSPipeline* pLine;
                if ((pLine = GSMain::getInstance().getPipeLine(mTag)) != NULL)
                    pLine->start();
            }

            //------------------------------------------------------

            void VideoWrapper::pause() {
                GSPipeline* pLine;
                if ((pLine = GSMain::getInstance().getPipeLine(mTag)) != NULL)
                    pLine->pause();
            }

            //------------------------------------------------------

            void VideoWrapper::stop() {
                GSPipeline* pLine;
                if ((pLine = GSMain::getInstance().getPipeLine(mTag)) != NULL)
                    pLine->stop();
            }

            //------------------------------------------------------

            void VideoWrapper::setWindow(ANativeWindow * view) {
                GstElement *videoSink = gst_bin_get_by_interface(GST_BIN(GSMain::getInstance().getPipeLine(mTag)->getPipeLine()), GST_TYPE_VIDEO_OVERLAY);

                gst_video_overlay_set_window_handle(GST_VIDEO_OVERLAY(videoSink), (guintptr) view);
            }

            //------------------------------------------------------

            void VideoWrapper::exposeVideoOverlay() {
                gst_video_overlay_expose (GST_VIDEO_OVERLAY (GSMain::getInstance().getPipeLine(mTag)->getPipeLine()));
            }
        }
    }
}
