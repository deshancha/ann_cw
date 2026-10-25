#include "AudioWrapper.h"
#include "GSMain.h"
#include <string>
#include "Defs.h"
#include "DatatoCGImageRef.h"
#include "DatatoCVPixelBufferRef.h"
#include "GSPipeline.h"

namespace AvatarIniOS
{
    namespace wrapper {
    
        AudioWrapper::AudioWrapper(id <PAudioWrapperDelegate> delegate, TAG& t, NSString* pipeLine) :
            mTag(t),
            mPipeLine(pipeLine){
            this->delegate = delegate;
        }

        //------------------------------------------------------

        AudioWrapper::~AudioWrapper() {
            stop();
            delegate = nil;
        }

        //------------------------------------------------------

        void AudioWrapper::hasMessage(TAG &tag, gchar *message) {
            NSString *string = [NSString stringWithUTF8String:message];
            [delegate hasAudioMessage:tag msg:string];
        }

        //------------------------------------------------------

        void AudioWrapper::init() {
            core::GSMain::getInstance().createPipeLine(this, mTag, [mPipeLine UTF8String])->init();
        }

        //------------------------------------------------------

        void AudioWrapper::play() {
            core::GSPipeline* pLine;
            if ((pLine = core::GSMain::getInstance().getPipeLine(mTag)) != NULL)
                pLine->start();
        }

        //------------------------------------------------------

        void AudioWrapper::stop() {
            core::GSPipeline* pLine;
            if ((pLine = core::GSMain::getInstance().getPipeLine(mTag)) != NULL)
                pLine->stop();
        }

        //------------------------------------------------------

    }
}
