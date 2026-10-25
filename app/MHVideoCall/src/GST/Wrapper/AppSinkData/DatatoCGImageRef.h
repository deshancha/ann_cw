#ifndef DATATO_CGIMAGEREF_H
#define DATATO_CGIMAGEREF_H

#import <Foundation/Foundation.h>
#include "IDataConvert.h"

namespace AvatarIniOS
{
    namespace wrapper {
        // Apple Core Graphics conversion
        class DatatoCGImageRef : public IDataConvert
        {
            
        public:
            void dataConvert(TAG &tag, GstVideoInfo &videoInfo, GstMapInfo &mapInfo, id <PDataConversionDelegate> delegate);
        };
    }
}
#endif
