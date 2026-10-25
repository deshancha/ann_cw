//
//  CoreMLSegmenter.h
//  core_ios
//
//  Created by Chamika Deshan on 25/10/26.
//

#import <Foundation/Foundation.h>
#import <CoreVideo/CoreVideo.h>
#import <CoreML/CoreML.h>
#import <Vision/Vision.h>

NS_ASSUME_NONNULL_BEGIN

@interface CoreMLSegmenter : NSObject

@property (nonatomic, readonly) BOOL isReady;

- (instancetype)init;


- (nullable CVPixelBufferRef)segmentPixelBuffer:(CVPixelBufferRef)inputPixelBuffer CF_RETURNS_RETAINED;

- (nullable CVPixelBufferRef)segmentRGBData:(const unsigned char *)rgbData
                                     width:(size_t)width
                                    height:(size_t)height CF_RETURNS_RETAINED;

@end

NS_ASSUME_NONNULL_END
