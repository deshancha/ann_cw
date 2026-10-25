//
//  PWrapperDelegate.h
//  Basic
//
//  Created by Chamika Deshan on 8/23/20.
//

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#include <gst/video/video.h>
#include "Defs.h"

NS_ASSUME_NONNULL_BEGIN

@protocol PVideoWrapperDelegate <NSObject>

// For CG Drawing
//-(void) receivedImage:(UIImage *)image;

// For OpenGL
//-(void) receivedCVPixelBufferRef:(CVPixelBufferRef)ref;

-(void) receivedVideoData:(TAG &)tag videoInfo:(GstVideoInfo&)videoInfo mapInfo:(GstMapInfo &)mapInfo;

-(void) hasVideoMessage:(TAG &)tag msg:(NSString *)message;

@end

//------------------------------------------

@protocol PAudioWrapperDelegate <NSObject>

-(void) hasAudioMessage:(TAG &)tag msg:(NSString *)message;

@end

//------------------------------------------

@protocol PCoreWrapperDelegate <NSObject>

-(void) gstInitialized;

@end

NS_ASSUME_NONNULL_END
