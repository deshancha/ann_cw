#include "GSPDecoratorGLSink.h"
#include "IGSTCallback.h"

namespace AvatarIniOS
{
    namespace core {
    
        //------------------------------------------------------

        GSPDecoratorGLSink::GSPDecoratorGLSink(GSPipeline *inner, guintptr renderViewId) : GSPipelineDecorator(inner), mRenderViewId(renderViewId){
            
        }

        //------------------------------------------------------

        GSPDecoratorGLSink::~GSPDecoratorGLSink() {
        }

        //------------------------------------------------------
    
        void GSPDecoratorGLSink::init() {
            
            GSPipelineDecorator::init();
            
            GstElement *videoSink = gst_bin_get_by_interface(GST_BIN(GSPipelineDecorator::getPipeLine()), GST_TYPE_VIDEO_OVERLAY);
            
            gst_video_overlay_set_window_handle(GST_VIDEO_OVERLAY(videoSink), mRenderViewId); //(guintptr) (id) mConf.glSinkRenderView
        }
    }
}
