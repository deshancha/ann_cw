#include "GSPDecoratorAppsink.h"
#include "IGSTCallback.h"

#include <boost/thread/thread.hpp>
#include <boost/thread/xtime.hpp>
#include <boost/preprocessor/stringize.hpp>


namespace AvatarIniOS {
    namespace core {

        //-----------

        template<class T>
        Async<T>::Async(T *pInstance, CallbackMethod pMethod):
                mInstance(pInstance),
                mMethod(pMethod) {
            isDone = false;
        }

        //-----------

        template<class T>
        void Async<T>::update() {

            boost::mutex mutex;
            boost::mutex::scoped_lock lock(mutex);

            while (!isDone) {
                mWakeCondition.wait(lock);
                if (isDone) break;
                (mInstance->*mMethod)();
            }
        }

        //-----------

        template<class T>
        void Async<T>::wake() {
            this->mWakeCondition.notify_one();
        }

        //----------------GSPDecoratorAppsink------------------

        GSPDecoratorAppsink::GSPDecoratorAppsink(GSPipeline *inner) : GSPipelineDecorator(inner) {
            mAppSink = NULL;
            asyncWork = new Async<GSPDecoratorAppsink>(this,
                                                       &GSPDecoratorAppsink::handleCallbackUpdates);

            mDataCallback = static_cast<IGSTDataCallback *>(GSPipelineDecorator::getCallback());

            this->startAppSinkReader();
        }

        //------------------------------------------------------

        GSPDecoratorAppsink::~GSPDecoratorAppsink() {
        }

        //------------------------------------------------------

        void GSPDecoratorAppsink::deInit() {
            boost::mutex::scoped_lock lock(asyncWork->mSharedMutex);
            callbackIdentifier = CALLBACK_IDEITIFIER_NONE;
            lock.unlock();

            asyncWork->isDone = true;
            asyncWork->wake();

            GSPipelineDecorator::deInit();

            mAppSink = NULL;
            delete asyncWork;
        }

        //------------------------------------------------------

        void GSPDecoratorAppsink::init() {
            GSPipelineDecorator::init();

            GstElement *sink = gst_bin_get_by_name(GST_BIN(GSPipelineDecorator::getPipeLine()),
                                                   "sink");

            mAppSink = GST_APP_SINK_CAST(sink);

            GstAppSinkCallbacks appsinkCallbacks;
            appsinkCallbacks.new_preroll = &GSPDecoratorAppsink::callBackNewPreroll;
            appsinkCallbacks.new_sample = &GSPDecoratorAppsink::callBackNewSample;

            gst_app_sink_set_callbacks(mAppSink, &appsinkCallbacks, this, nullptr);
        }

        //------------------------------------------------------

        GstFlowReturn
        GSPDecoratorAppsink::callBackNewPreroll(GstAppSink *appSink, gpointer userData) {
            GSPDecoratorAppsink *pipeline = static_cast<GSPDecoratorAppsink *>(userData);

            boost::mutex::scoped_lock lock(pipeline->asyncWork->mSharedMutex);
            pipeline->callbackIdentifier = CALLBACK_IDEITIFIER_NEW_PREROLL;
            lock.unlock();

            pipeline->asyncWork->wake();

            return GST_FLOW_OK;
        }

        //------------------------------------------------------

        GstFlowReturn
        GSPDecoratorAppsink::callBackNewSample(GstAppSink *appSink, gpointer userData) {

            GSPDecoratorAppsink *pipeline = static_cast<GSPDecoratorAppsink *>(userData);

            boost::mutex::scoped_lock lock(pipeline->asyncWork->mSharedMutex);
            pipeline->callbackIdentifier = CALLBACK_IDEITIFIER_NEW_SAMPLE;
            lock.unlock();

            pipeline->asyncWork->wake();

            return GST_FLOW_OK;
        }

        //------------------------------------------------------

        void GSPDecoratorAppsink::startAppSinkReader() {
            PIPELINE_INFO(this, "Appsink Async Read Start...");
            boost::thread(&Async<GSPDecoratorAppsink>::update, asyncWork);

        }

        //------------------------------------------------------

        void GSPDecoratorAppsink::handleCallbackUpdates() {
            int serveCallbackIdentifier;

            boost::mutex::scoped_lock lock(asyncWork->mSharedMutex);
            serveCallbackIdentifier = callbackIdentifier;
            callbackIdentifier = CALLBACK_IDEITIFIER_NONE;
            lock.unlock();

            switch (serveCallbackIdentifier) {
                case CALLBACK_IDEITIFIER_NEW_PREROLL: {
                    //Below need? Why? Without this sometimes fails
                    GstSample *sample = gst_app_sink_pull_preroll(mAppSink);
                    this->handleVideoSample(sample, false);
                    gst_sample_unref(sample);
                    break;
                }
                case CALLBACK_IDEITIFIER_NEW_SAMPLE: {
                    GstSample *sample = gst_app_sink_pull_sample(mAppSink);
                    this->handleVideoSample(sample, true);
                    gst_sample_unref(sample);
                    break;
                }
                default:
                    break;
            }
        }

        //------------------------------------------------------

        void GSPDecoratorAppsink::handleVideoSample(GstSample *sample, bool display) {
            GstBuffer *buffer = gst_sample_get_buffer(sample);

            if (!buffer)
                return;

            GstVideoInfo videoInfo = getVideoInfo(sample);

            GstMapInfo mapInfo;

            if (gst_buffer_map(buffer, &mapInfo, GST_MAP_READ)) {

                if (display) {
                    mDataCallback->hasData(this->getTag(), videoInfo, mapInfo);
                }
                gst_buffer_unmap(buffer, &mapInfo);
            }
        }

        //------------------------------------------------------

        GstVideoInfo GSPDecoratorAppsink::getVideoInfo(GstSample *sample) {
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
