//
//  VideoConsumerContour.m
//  Call-App
//
//  Created by Chamika Deshan on 2/9/22.
//

#import "MLContour.h"
#include "Defs.h"
#include <gst/video/video.h>
#include "AppLog.h"

@implementation MLContour

-(id) init:(NSString*) modelName delegate:(id <PHasMaskDelegate>)maskDelegate {
    return [self initWithDelegate:maskDelegate];
}

-(id) initWithDelegate:(id <PHasMaskDelegate>)maskDelegate {
    self = [super init];
    if (self) {
        self->delegate = maskDelegate;
        segmenter = [[CoreMLSegmenter alloc] init];
        if (segmenter.isReady) {
            appLogger.logInfo("CoreML UNet MobileNet model loaded successfully");
        } else {
            appLogger.logError("Failed to load CoreML UNet model");
        }
    }
    return self;
}

//---------------------------------------------------
    
-(void) receivedVideoData:(TAG &)tag videoInfo:(GstVideoInfo&)videoInfo mapInfo:(GstMapInfo &)mapInfo {
    unsigned char* videoData = mapInfo.data;
    int videoWidth = videoInfo.width;
    int videoHeight = videoInfo.height;

    CVPixelBufferRef maskPixelBuffer = [segmenter segmentRGBData:videoData
                                                           width:videoWidth
                                                          height:videoHeight];
    if (maskPixelBuffer == NULL) {
        return;
    }

    [self->delegate hasMask:maskPixelBuffer];

    if (_maskImageView) {
        @autoreleasepool {
            CIImage *ciImage = [CIImage imageWithCVPixelBuffer:maskPixelBuffer];
            UIImage *uiImage = [UIImage imageWithCIImage:ciImage];

            dispatch_async(dispatch_get_main_queue(), ^{
                self->_maskImageView.image = uiImage;
            });
        }
    }

    CVPixelBufferRelease(maskPixelBuffer);
}

//---------------------------------------------------

- (void)hasVideoMessage:(TAG &)tag msg:(nonnull NSString *)message {
    NSString *pipeLineTag = [NSString stringWithUTF8String:tag.c_str()];
    NSLog(@"Message From Pipeline: %@, msg : %@", pipeLineTag, message);
}

//---------------------------------------------------

-(void) clear {
    segmenter = nil;
}

@end
