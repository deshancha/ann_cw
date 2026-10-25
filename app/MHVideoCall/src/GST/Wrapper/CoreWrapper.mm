#include "CoreWrapper.h"
#include "GSMain.h"
#include <string>
#include "Defs.h"

namespace AvatarIniOS
{
    namespace wrapper {
    
        CoreWrapper::CoreWrapper(id <PCoreWrapperDelegate> delegate){
            this->delegate = delegate;
        }

        //------------------------------------------------------

        CoreWrapper::~CoreWrapper() {
            stopAllPipeLines();
            delegate = nil;
        }

        //------------------------------------------------------

        void CoreWrapper::gstInitialized() {
            [delegate gstInitialized];
        }


        //------------------------------------------------------

        void CoreWrapper::initGStreamer() {
            core::GSMain::getInstance().initGStreamer();
        }

        //------------------------------------------------------

        void CoreWrapper::startMain() {
            dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{
                core::GSMain::getInstance().startMainLoop(this);
            });
        }

        //------------------------------------------------------

        void CoreWrapper::stopAllPipeLines() {
            core::GSMain::getInstance().stopAllPipeLines();
        }

        //------------------------------------------------------
    }
}
