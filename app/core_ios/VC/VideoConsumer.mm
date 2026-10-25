//
//  VideoConsumer.m
//  core_ios
//
//  Created by Chamika Deshan on 9/21/20.
//

#import "VideoConsumer.h"
#include "IDataConvert.h"
#include "DatatoCVPixelBufferRef.h"

using namespace AvatarIniOS::wrapper;

@interface VideoConsumer () <PDataConversionDelegate>
{
    IDataConvert* dataConverter;
    NSObject* maskLock;
    
    CVPixelBufferRef maskPixelBuffer;
}
@end

@implementation VideoConsumer

@synthesize appSinkGLView;

-(id) init {
    self = [super init];
    
    if (self) {
        maskLock = [[NSObject alloc] init];
        maskPixelBuffer = NULL;
    }
    
    return self;
}


-(UIView*) makeRenderView: (RenderType) renderType frame:(CGRect) frame {
    UIView *currentRenderView = nil;
    
    switch (renderType) {
        case APPSINK_OPENGL:
            dataConverter = static_cast<IDataConvert*>(new DatatoCVPixelBufferRef());
            self->appSinkGLView = [[AppSinkGLView alloc] initWithFrame:frame];
            appSinkGLView.backgroundColor = [UIColor greenColor];
            currentRenderView = self->appSinkGLView;
            
            [appSinkGLView setupGL];
            appSinkGLView.presentationRect = CGSizeMake(1280, 720);
            break;
        default:
            break;
    }
    
    return currentRenderView;
}

//---------------------------------------------------

-(void) clean {
    delete dataConverter;
    dataConverter = NULL;
    @synchronized (maskLock) {
        if (maskPixelBuffer != NULL) {
            CVPixelBufferRelease(maskPixelBuffer);
            maskPixelBuffer = NULL;
        }
    }
}

- (void)dealloc {
    [self clean];
}

//---------------------------------------------------
    
-(void) receivedVideoData:(TAG &)tag videoInfo:(GstVideoInfo&)videoInfo mapInfo:(GstMapInfo &)mapInfo {
    if (dataConverter) {
        dataConverter->dataConvert(tag, videoInfo, mapInfo, self);
    }
}

//---------------------------------------------------
- (void)hasVideoMessage:(TAG &)tag msg:(nonnull NSString *)message {
    NSString *pipeLineTag = [NSString stringWithUTF8String:tag.c_str()];
    NSLog(@"Message From Pipeline: %@, msg : %@", pipeLineTag, message);
}

//---------------------------------------------------

-(void) receivedCVPixelBufferRef:(CVPixelBufferRef)ref {
    @synchronized (maskLock) {
        [appSinkGLView displayPixelBuffer:ref mask:maskPixelBuffer];
    }
    //[appSinkGLView displayPixelBuffer:ref];
}

//---------------------------------------------------

- (void)receivedImage:(nonnull UIImage *)image {
}

-(void) hasMask:(CVPixelBufferRef)maskRef {
    @synchronized (maskLock) {
        
        if (maskPixelBuffer != NULL) {
            CVPixelBufferRelease(maskPixelBuffer);
            maskPixelBuffer = NULL;
        }
        if (maskRef != NULL) {
            CVPixelBufferRetain(maskRef);
            maskPixelBuffer = maskRef;
        }
    }
}


@end
