#include "VideoWrapper.h"
#include "GSMain.h"
#include <string>
#include "Defs.h"
#include "GSPipeline.h"
#include "GSPipelineBuilder.h"

namespace AvatarIniOS
{
    namespace wrapper {
    
        VideoWrapper::VideoWrapper(id <PVideoWrapperDelegate> delegate, TAG& t, NSString* pipeLine, RenderType renderType, UIView* view) :
        mTag(t),
        mRenderType(renderType),
        mUIView(view),
        mPipeLine(pipeLine){
            this->delegate = delegate;
        }

        //------------------------------------------------------

        VideoWrapper::~VideoWrapper() {
            stop();
            delegate = nil;
            mUIView = NULL;
        }

        //------------------------------------------------------

        void VideoWrapper::hasData(TAG &tag, GstVideoInfo &videoInfo, GstMapInfo &mapInfo) {
            [delegate receivedVideoData:tag videoInfo:videoInfo mapInfo:mapInfo];
            //dataConverter->dataConvert(tag, videoInfo, mapInfo, delegate);
        }

        //------------------------------------------------------

        void VideoWrapper::hasMessage(TAG &tag, gchar *message) {
            NSString *string = [NSString stringWithUTF8String:message];
            [delegate hasVideoMessage:tag msg:string];
        }

        //------------------------------------------------------

        void VideoWrapper::init() {
            
            if (mRenderType == APPSINK_OPENGL || mRenderType == APPSINK_CG) {
                core::GSMain::getInstance().createAppsinkPipeLine(this, mTag, [mPipeLine UTF8String])->init();
            } else if (mRenderType == GLSINK && mUIView != NULL) {
                
                NSError *error = nil;
                NSString *fragShader = [[NSString alloc] initWithContentsOfURL:[[NSBundle bundleWithIdentifier: @"com.novubits..MHVideoCall"] URLForResource:@"GLSink" withExtension:@"fsh"] encoding:NSUTF8StringEncoding error:&error];
                
                error = nil;
                if (error) {
                    NSLog(@"Shader Load Failed: %@", [error debugDescription]);
                }
                
                NSString *vertShader = [[NSString alloc] initWithContentsOfURL:[[NSBundle bundleWithIdentifier: @"com.novubits..MHVideoCall"] URLForResource:@"GLSink" withExtension:@"vsh"] encoding:NSUTF8StringEncoding error:&error];
                
                if (error) {
                    NSLog(@"Shader Load Failed: %@", [error debugDescription]);
                }
                
                core::GSMain::getInstance().createGLSinkPipeLine(this, mTag, [mPipeLine UTF8String], (guintptr) (id) mUIView, [fragShader UTF8String], [vertShader UTF8String] )->init();
            } else {
                // eg: No sink video sender
                core::GSMain::getInstance().createPipeLine(this, mTag, [mPipeLine UTF8String])->init();
            }
        }

        //------------------------------------------------------

        void VideoWrapper::play() {
            core::GSPipeline* pLine;
            if ((pLine = core::GSMain::getInstance().getPipeLine(mTag)) != NULL)
                pLine->start();
        }

        //------------------------------------------------------

        void VideoWrapper::stop() {
            core::GSPipeline* pLine;
            if ((pLine = core::GSMain::getInstance().getPipeLine(mTag)) != NULL)
                pLine->stop();
        }

        //------------------------------------------------------

    }
}
