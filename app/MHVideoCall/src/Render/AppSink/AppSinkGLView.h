

#import <UIKit/UIKit.h>

@interface AppSinkGLView : UIView

@property CGSize presentationRect;

- (void)setupGL;

- (void)displayPixelBuffer:(CVPixelBufferRef)pixelBuffer;

- (void)displayPixelBuffer:(CVPixelBufferRef)pixelBuffer mask:(CVPixelBufferRef)mask;

- (void) setShift:(float)val;

- (void) setRotate:(float)val;

- (void) enableMask:(BOOL) val;

- (void) setMaskPivotX:(float) x pivotY:(float) y;

- (void) depthPopShift;

- (void) nextBackground;

@end
