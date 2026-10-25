//
//  CoreMLSegmenter.mm
//  core_ios
//
//  Created on 2026-10-25.
//

#import "CoreMLSegmenter.h"
#import "UNetMobileNetV1Full.h"

@interface CoreMLSegmenter () {
  VNCoreMLModel *_visionModel;
  VNCoreMLRequest *_coreMLRequest;
  NSLock *_lock;
}
@end

@implementation CoreMLSegmenter

- (instancetype)init {
  self = [super init];
  if (self) {
    _lock = [[NSLock alloc] init];
    _isReady = [self setupModel];
  }
  return self;
}

- (BOOL)setupModel {
  NSError *error = nil;
  MLModelConfiguration *config = [[MLModelConfiguration alloc] init];
  config.computeUnits = MLComputeUnitsAll;

  MLModel *mlModel = nil;

  // 1. Try loading via Xcode-generated wrapper class
  UNetMobileNetV1Full *wrapper =
      [[UNetMobileNetV1Full alloc] initWithConfiguration:config error:&error];
  if (wrapper && wrapper.model) {
    mlModel = wrapper.model;
  }

  // 2. Fallback to compiled bundle resource if wrapper failed
  if (!mlModel) {
    NSURL *modelURL =
        [[NSBundle mainBundle] URLForResource:@"UNetMobileNetV1Full"
                                withExtension:@"mlmodelc"];
    if (modelURL) {
      mlModel = [MLModel modelWithContentsOfURL:modelURL
                                  configuration:config
                                          error:&error];
    }
  }

  if (!mlModel) {
    NSLog(@"[CoreMLSegmenter] Failed to load UNetMobileNetV1Full model: %@",
          error);
    return NO;
  }

  _visionModel = [VNCoreMLModel modelForMLModel:mlModel error:&error];
  if (!_visionModel) {
    NSLog(@"[CoreMLSegmenter] Failed to create VNCoreMLModel: %@", error);
    return NO;
  }

  _coreMLRequest = [[VNCoreMLRequest alloc] initWithModel:_visionModel];
  _coreMLRequest.imageCropAndScaleOption = VNImageCropAndScaleOptionScaleFill;

  NSLog(@"[CoreMLSegmenter] Successfully initialized UNetMobileNetV1Full "
        @"CoreML engine on ANE/GPU");
  return YES;
}

- (nullable CVPixelBufferRef)segmentPixelBuffer:
    (CVPixelBufferRef)inputPixelBuffer {
  if (!inputPixelBuffer || !_isReady) {
    return NULL;
  }

  [_lock lock];
  @try {
    VNImageRequestHandler *handler =
        [[VNImageRequestHandler alloc] initWithCVPixelBuffer:inputPixelBuffer
                                                     options:@{}];
    NSError *error = nil;
    BOOL success = [handler performRequests:@[ _coreMLRequest ] error:&error];
    if (!success || error) {
      NSLog(@"[CoreMLSegmenter] performRequests error: %@", error);
      return NULL;
    }

    CVPixelBufferRef outputBuffer =
        [self extractPixelBufferFromResults:_coreMLRequest.results];
    if (outputBuffer) {
      CVPixelBufferRetain(outputBuffer);
      return outputBuffer;
    }
  } @catch (NSException *exception) {
    NSLog(@"[CoreMLSegmenter] Exception during segmentation: %@", exception);
  } @finally {
    [_lock unlock];
  }

  return NULL;
}

- (nullable CVPixelBufferRef)segmentRGBData:(const unsigned char *)rgbData
                                      width:(size_t)width
                                     height:(size_t)height {
  if (!rgbData || width == 0 || height == 0 || !_isReady) {
    return NULL;
  }

  NSDictionary *pixelAttributes =
      @{(NSString *)kCVPixelBufferIOSurfacePropertiesKey : @{}};

  CVPixelBufferRef inputPixelBuffer = NULL;
  CVReturn status = CVPixelBufferCreate(
      kCFAllocatorDefault, width, height, kCVPixelFormatType_32BGRA,
      (__bridge CFDictionaryRef)pixelAttributes, &inputPixelBuffer);

  if (status != kCVReturnSuccess || !inputPixelBuffer) {
    NSLog(@"[CoreMLSegmenter] Failed to create input CVPixelBuffer: %d",
          status);
    return NULL;
  }

  CVPixelBufferLockBaseAddress(inputPixelBuffer, 0);
  uint8_t *baseAddress =
      (uint8_t *)CVPixelBufferGetBaseAddress(inputPixelBuffer);
  size_t bytesPerRow = CVPixelBufferGetBytesPerRow(inputPixelBuffer);

  // Convert packed 24-bit RGB (from GStreamer) -> 32-bit BGRA (natively
  // supported by Vision & CoreML), withou this ipad pro 10.5 failed
  for (size_t y = 0; y < height; y++) {
    const uint8_t *srcRow = rgbData + y * width * 3;
    uint8_t *dstRow = baseAddress + y * bytesPerRow;
    for (size_t x = 0; x < width; x++) {
      uint8_t r = srcRow[x * 3 + 0];
      uint8_t g = srcRow[x * 3 + 1];
      uint8_t b = srcRow[x * 3 + 2];
      dstRow[x * 4 + 0] = b;
      dstRow[x * 4 + 1] = g;
      dstRow[x * 4 + 2] = r;
      dstRow[x * 4 + 3] = 255;
    }
  }
  CVPixelBufferUnlockBaseAddress(inputPixelBuffer, 0);

  CVPixelBufferRef maskBuffer = [self segmentPixelBuffer:inputPixelBuffer];
  CVPixelBufferRelease(inputPixelBuffer);

  return maskBuffer;
}

- (nullable CVPixelBufferRef)extractPixelBufferFromResults:(NSArray *)results {
  if (!results || results.count == 0) {
    return NULL;
  }

  id first = results.firstObject;
  if ([first isKindOfClass:[VNPixelBufferObservation class]]) {
    VNPixelBufferObservation *obs = (VNPixelBufferObservation *)first;
    return obs.pixelBuffer;
  }

  if ([first isKindOfClass:[VNCoreMLFeatureValueObservation class]]) {
    VNCoreMLFeatureValueObservation *featureObs =
        (VNCoreMLFeatureValueObservation *)first;
    if (featureObs.featureValue.imageBufferValue) {
      return featureObs.featureValue.imageBufferValue;
    }
  }

  return NULL;
}

@end
