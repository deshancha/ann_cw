//
//  VideoConsumer.m
//  core_ios
//
//  Created by Chamika Deshan on 9/21/20.
//

#import "VideoConsumer.h"
#import <QuartzCore/QuartzCore.h>
#include "IDataConvert.h"
#include "DatatoCVPixelBufferRef.h"

using namespace AvatarIniOS::wrapper;

@interface VideoConsumer () <PDataConversionDelegate>
{
    IDataConvert* dataConverter;
    NSObject* maskLock;
    
    CVPixelBufferRef maskPixelBuffer;
    
    NSObject* fpsLock;
    NSInteger _videoFrameCount;
    NSInteger _maskFrameCount;
    NSTimeInterval _lastFPSTime;
}
@end

@implementation VideoConsumer

@synthesize appSinkGLView;

-(id) init {
    self = [super init];
    
    if (self) {
        maskLock = [[NSObject alloc] init];
        maskPixelBuffer = NULL;
        fpsLock = [[NSObject alloc] init];
        _videoFrameCount = 0;
        _maskFrameCount = 0;
        _lastFPSTime = 0;
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
    self.onFPSUpdate = nil;
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

- (void)updateFPSForVideoFrame:(BOOL)isVideo {
    @synchronized (fpsLock) {
        if (isVideo) {
            _videoFrameCount++;
        } else {
            _maskFrameCount++;
        }
        
        NSTimeInterval now = CACurrentMediaTime();
        if (_lastFPSTime == 0) {
            _lastFPSTime = now;
            return;
        }
        
        NSTimeInterval elapsed = now - _lastFPSTime;
        if (elapsed >= 1.0) {
            NSInteger videoFPS = (NSInteger)round(_videoFrameCount / elapsed);
            NSInteger maskFPS = (NSInteger)round(_maskFrameCount / elapsed);
            
            _videoFrameCount = 0;
            _maskFrameCount = 0;
            _lastFPSTime = now;
            
            if (self.onFPSUpdate) {
                VideoConsumerFPSBlock block = self.onFPSUpdate;
                dispatch_async(dispatch_get_main_queue(), ^{
                    block(videoFPS, maskFPS);
                });
            }
        }
    }
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
    [self updateFPSForVideoFrame:YES];
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
    //[NSThread sleepForTimeInterval:0.05];
    [self updateFPSForVideoFrame:NO];
}


@end
