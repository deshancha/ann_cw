#ifndef GST_MAIN_CALLBACK_H
#define GST_MAIN_CALLBACK_H

#include "Defs.h"

namespace AvatarIniOS
{
    namespace core {
        class IGSTMainCallback {
           public:
                virtual void gstInitialized()= 0;
        };
    }
}

#endif
