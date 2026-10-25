#include "GSPDecoratorAppsink.h"
#include "IGSTCallback.h"
#import <Foundation/Foundation.h>

namespace AvatarIniOS
{
    namespace core {
    
        class Async {
        public:
            dispatch_semaphore_t semaphore;
            NSObject* lockObject;
            
            Async()
            {
                semaphore = dispatch_semaphore_create(0);
                lockObject = [[NSObject alloc] init];
            }
        };
    
        //------------------------------------------------------

        GSPDecoratorAppsink::GSPDecoratorAppsink(GSPipeline *inner) : GSPipelineDecorator(inner) {
            mAppSink = NULL;
            asyncWork = new Async();
            isDone = false;
            mDataCallback = static_cast<IGSTDataCallback*>(GSPipelineDecorator::getCallback());
            
            this->startAppSinkReader();
        }

        //------------------------------------------------------

        GSPDecoratorAppsink::~GSPDecoratorAppsink() {
            NSLog(@"~GSPDecoratorAppsink");
        }

        //------------------------------------------------------

        void GSPDecoratorAppsink::deInit()
        {
            NSLog(@"~GSPDecoratorAppsink");
            @synchronized(asyncWork->lockObject) {
                callbackIdentifier =  CALLBACK_IDEITIFIER_NONE;
            }
            isDone = true;
            dispatch_semaphore_signal(asyncWork->semaphore);
            
           GSPipelineDecorator::deInit();
            
            mAppSink = NULL;
            delete asyncWork;
        }
    
        //------------------------------------------------------
    
        void GSPDecoratorAppsink::init() {
            GSPipelineDecorator::init();
            
            GstElement* sink = gst_bin_get_by_name(GST_BIN(GSPipelineDecorator::getPipeLine()), "sink");
                
            //mAppSink = GST_APP_SINK_CAST(sink);
            
            mAppSink = GST_APP_SINK(sink);
            if (!mAppSink) {
                NSLog(@"Error Appsink");
                return;
            }
            
            union {
                GstAppSinkCallbacks callbacks;
                char padding[64];
              } gstCallbacks;
            
            memset(gstCallbacks.padding, 0, sizeof(gstCallbacks.padding));
            
            gstCallbacks.callbacks.new_preroll = &GSPDecoratorAppsink::callBackNewPreroll;
            gstCallbacks.callbacks.new_sample = &GSPDecoratorAppsink::callBackNewSample;
            
//            GstAppSinkCallbacks appsinkCallbacks;
//            appsinkCallbacks.new_preroll    = &GSPDecoratorAppsink::callBackNewPreroll;
//            appsinkCallbacks.new_sample        = &GSPDecoratorAppsink::callBackNewSample;
            
            gst_app_sink_set_callbacks(GST_APP_SINK(mAppSink), &gstCallbacks.callbacks, this, NULL);

            //gst_app_sink_set_callbacks(mAppSink, &appsinkCallbacks, this, nullptr);
        }
    
        //------------------------------------------------------

        GstFlowReturn GSPDecoratorAppsink::callBackNewPreroll(GstAppSink *appSink, gpointer userData)
        {
            NSLog(@"callBackNewPreroll 1");
            GSPDecoratorAppsink* pipeline = static_cast<GSPDecoratorAppsink*>(userData);

            @synchronized(pipeline->asyncWork->lockObject) {
                pipeline->callbackIdentifier = CALLBACK_IDEITIFIER_NEW_PREROLL;
            }
            dispatch_semaphore_signal(pipeline->asyncWork->semaphore);

            return GST_FLOW_OK;
        }

        //------------------------------------------------------

        GstFlowReturn GSPDecoratorAppsink::callBackNewSample(GstAppSink *appSink, gpointer userData)
        {
            NSLog(@"callBackNewSample 1");
            
            GSPDecoratorAppsink* pipeline = static_cast<GSPDecoratorAppsink*>(userData);

            @synchronized(pipeline->asyncWork->lockObject) {
                pipeline->callbackIdentifier = CALLBACK_IDEITIFIER_NEW_SAMPLE;
            }
            dispatch_semaphore_signal(pipeline->asyncWork->semaphore);

            return GST_FLOW_OK;
        }

        //------------------------------------------------------

        void GSPDecoratorAppsink::startAppSinkReader() {
            dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{
                PIPELINE_INFO(this, "Appsink Async Read Start...");
                while (!isDone) {
                    NSLog(@"startAppSinkReader 1");
                    dispatch_semaphore_wait(asyncWork->semaphore, DISPATCH_TIME_FOREVER);
                    if(isDone) break;
                    NSLog(@"startAppSinkReader 2");
                    this->handleCallbackUpdates();
                }

                PIPELINE_INFO(this, "Appsink Async Read Stopped");
            });
        }

        //------------------------------------------------------

        void GSPDecoratorAppsink::handleCallbackUpdates()
        {
            NSLog(@"handleCallbackUpdates 1");
            int serveCallbackIdentifier;


            @synchronized(asyncWork->lockObject) {
                serveCallbackIdentifier = callbackIdentifier;
                callbackIdentifier =  CALLBACK_IDEITIFIER_NONE;
            }

            switch(serveCallbackIdentifier) {
                case CALLBACK_IDEITIFIER_NEW_PREROLL:
                {
                    /*Below need? Why? Without this sometimes fails*/
                    GstSample* sample = gst_app_sink_pull_preroll(mAppSink);
                    this->handleVideoSample(sample, false);
                    gst_sample_unref(sample);
                    break;
                }
                case CALLBACK_IDEITIFIER_NEW_SAMPLE:
                {
                    GstSample* sample = gst_app_sink_pull_sample(mAppSink);
                    this->handleVideoSample(sample, true);
                    gst_sample_unref(sample);
                    break;
                }
                default:
                    break;
            }
        }

        //------------------------------------------------------

        void GSPDecoratorAppsink::handleVideoSample(GstSample* sample, bool display)
        {
            NSLog(@"handleVideoSample 1");
            GstBuffer* buffer = gst_sample_get_buffer(sample);

            if(!buffer)
                return;
            
            GstVideoInfo videoInfo = getVideoInfo(sample);

            GstMapInfo mapInfo;

            if(gst_buffer_map(buffer, &mapInfo, GST_MAP_READ)) {

                if (display) {
                    mDataCallback->hasData(this->getTag(), videoInfo, mapInfo);
                }
                gst_buffer_unmap(buffer, &mapInfo);
            }
        }

        //------------------------------------------------------

        GstVideoInfo GSPDecoratorAppsink::getVideoInfo(GstSample *sample) {
            NSLog(@"getVideoInfo 1");
            GstCaps *caps = gst_sample_get_caps(sample);
            GstVideoInfo vinfo;
            gst_video_info_init(&vinfo);
            if (caps) {
                gst_video_info_from_caps(&vinfo, caps);
            }
            return vinfo;
        }
    }
}
