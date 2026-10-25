#ifndef DATATO_CVPIXELBUFFERREF_H
#define DATATO_CVPIXELBUFFERREF_H

#import <Foundation/Foundation.h>
#include "IDataConvert.h"

namespace AvatarIniOS
{
    namespace wrapper {
        // YUV CVPixelBufferRef for OpenGL YUV texture generatgion
        class DatatoCVPixelBufferRef : public IDataConvert
        {
            
        public:
            void dataConvert(TAG &tag, GstVideoInfo &videoInfo, GstMapInfo &mapInfo, id <PDataConversionDelegate> delegate);
        };
    }
}

#endif
