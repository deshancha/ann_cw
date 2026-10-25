#include "CoreWrapper.h"
#include "GSMain.h"
#include <string>
#include "Defs.h"

namespace avatarflow {
    namespace wrapper {
        namespace android {

            CoreWrapper::CoreWrapper(IGSTMainCallback *cb) :
                    mCb(cb) {

            }

            //------------------------------------------------------

            CoreWrapper::~CoreWrapper() {
                mCb = NULL;
                //stopAllPipeLines();
                GSMain::getInstance().clearAllPipeLines();
            }

            //------------------------------------------------------

            void CoreWrapper::initGStreamer() {
                GSMain::getInstance().initGStreamer();
            }

            //------------------------------------------------------

            void CoreWrapper::startMain() {
                GSMain::getInstance().startMainLoop(mCb);
            }

            //------------------------------------------------------

            void CoreWrapper::stopAllPipeLines() {
                GSMain::getInstance().stopAllPipeLines();
            }
        }
    }
}
