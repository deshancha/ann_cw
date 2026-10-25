//
//  PWrapperDelegate.h
//  Basic
//
//  Created by Chamika Deshan on 8/23/20.
//

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>

NS_ASSUME_NONNULL_BEGIN

@protocol PDataConversionDelegate <NSObject>

// For CG Drawing
-(void) receivedImage:(UIImage *)image;

// For OpenGL
-(void) receivedCVPixelBufferRef:(CVPixelBufferRef)ref;

@end

NS_ASSUME_NONNULL_END
