#include "DatatoCGImageRef.h"
#include "Defs.h"

namespace AvatarIniOS
{
    namespace wrapper {
        //------------------------------------------------------

        void DatatoCGImageRef::dataConvert(TAG &tag, GstVideoInfo &videoInfo, GstMapInfo &mapInfo, id <PDataConversionDelegate> delegate) {
            
                gint width = videoInfo.width;
                gint height = videoInfo.height;
            
                if (width < 10 || height < 10) return;  // sometimes it comes 0 and 0, not sure why
                    
                NSDictionary *pixelAttributes = @{(NSString*)kCVPixelBufferIOSurfacePropertiesKey:@{}};
                
                CVPixelBufferRef pixelBuffer = NULL;
                
                CVReturn result = CVPixelBufferCreate(kCFAllocatorDefault,
                                                      width,
                                                      height,
                                                      kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange,
                                                      // kCVPixelFormatType_420YpCbCr8BiPlanarFullRange, \
                                                      kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange
                                                      (__bridge CFDictionaryRef)(pixelAttributes),
                                                      &pixelBuffer);
                
                CVPixelBufferLockBaseAddress(pixelBuffer,0);
                void *yDestPlane = CVPixelBufferGetBaseAddressOfPlane(pixelBuffer, 0);
                
                // Here y_ch0 is Y-Plane of YUV(NV12) data.
                unsigned char *y_ch0 = mapInfo.data;
                memcpy(yDestPlane, y_ch0, width * height);
                void *uvDestPlane = CVPixelBufferGetBaseAddressOfPlane(pixelBuffer, 1);
                
                // Here y_ch1 is UV-Plane of YUV(NV12) data.
                unsigned char *y_ch1 = mapInfo.data + width * height;
                memcpy(uvDestPlane, y_ch1, width * height/2);
                CVPixelBufferUnlockBaseAddress(pixelBuffer, 0);
                
                if (result != kCVReturnSuccess) {
                    NSLog(@"Unable to create cvpixelbuffer %d", result);
                    CVPixelBufferRelease(pixelBuffer);
                    return;
                }

                @autoreleasepool {
                    CIImage *ciImage = [CIImage imageWithCVPixelBuffer:pixelBuffer];
                    UIImage *uiImage = [UIImage imageWithCIImage:ciImage];
                    
                    dispatch_async(dispatch_get_main_queue(), ^{
                        [delegate receivedImage:uiImage];
                    });
                }
                CVPixelBufferRelease(pixelBuffer);
                    
                //printf("Appsink Data from PipeLine : %s, Width = %d, Height = %d\n", tag.c_str(), width, height);
        }
    }
}
