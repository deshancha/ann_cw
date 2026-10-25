#include "GSPipelineDecorator.h"
#include "IGSTCallback.h"
#include "GSPipelineBase.h"

namespace AvatarIniOS
{
    namespace core {
        //------------------------------------------------------

        GSPipelineDecorator::GSPipelineDecorator(GSPipeline *inner) : mGsPipeline(inner) {
        }

        //------------------------------------------------------

        GSPipelineDecorator::~GSPipelineDecorator() {
            // deletre decorator unless instance of GSPipelineBase
            if(GSPipelineBase* basePipeLine = dynamic_cast<GSPipelineBase*>(mGsPipeline)) {
                PIPELINE_INFO(this, "At Basepipeline Level Not Destroy");
                /* HERE WE DO NOT DELETE BasePipeline when decorator is used
                 * A referance to BasePipeline is kept in GSMain for
                 *      1. pipeline state management
                 *      2. Runtime Decorators
                 **/
                // The referance no need so release
                mGsPipeline = NULL;
            } else {
                PIPELINE_INFO(this, "Destroy");
                delete mGsPipeline;
                mGsPipeline = NULL;
            }
        }

        //------------------------------------------------------

        void GSPipelineDecorator::deInit()
        {
            mGsPipeline->deInit();
        }
    
        //------------------------------------------------------
    
        void GSPipelineDecorator::init()
        {
            mGsPipeline->init();
        }

        //------------------------------------------------------

        bool GSPipelineDecorator::start()
        {
            return mGsPipeline->start();
        }

        bool GSPipelineDecorator::pause() { return mGsPipeline->pause(); }

        //------------------------------------------------------

        bool GSPipelineDecorator::stop()
        {
            return mGsPipeline->stop();
        }

        //------------------------------------------------------

        void GSPipelineDecorator::clear() {
            mGsPipeline->clear();
        }
    }
}
