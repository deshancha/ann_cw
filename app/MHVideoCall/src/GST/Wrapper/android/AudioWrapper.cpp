#include "AudioWrapper.h"
#include "GSMain.h"
#include <string>
#include "Defs.h"
#include "GSPipeline.h"

namespace avatarflow {
    namespace wrapper {
        namespace android {

            AudioWrapper::AudioWrapper(IGSTCallback *cb, TAG &t,
                                       const char *pipeLine) :
                    mCb(cb),
                    mTag(t),
                    mPipeLine(pipeLine) {
            }

            //------------------------------------------------------

            AudioWrapper::~AudioWrapper() {
                mCb = NULL;
                //stop();
            }


            //------------------------------------------------------

            void AudioWrapper::init() {
                GSPipeline *decoratedPipeline =
                        GSMain::getInstance().createPipeLine(mCb, mTag, mPipeLine);

                decoratedPipeline->init();
                //delete decoratedPipeline;
            }

            //------------------------------------------------------

            void AudioWrapper::play() {
                GSPipeline *pLine;
                if ((pLine = GSMain::getInstance().getPipeLine(mTag)) != NULL)
                    pLine->start();
            }

            //------------------------------------------------------

            void AudioWrapper::pause() {
                GSPipeline *pLine;
                if ((pLine = GSMain::getInstance().getPipeLine(mTag)) != NULL)
                    pLine->pause();
            }

            //------------------------------------------------------

            void AudioWrapper::stop() {
                GSPipeline *pLine;
                if ((pLine = GSMain::getInstance().getPipeLine(mTag)) != NULL)
                    pLine->stop();
            }
        }
    }
}
