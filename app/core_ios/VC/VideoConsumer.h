//
//  VideoConsumer.h
//  core_ios
//
//  Created by Chamika Deshan on 9/21/20.
//

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#import "AppSinkGLView.h"
#import "PDataConversionDelegate.h"
#import "PWrapperDelegate.h"
#include "Defs.h"
#import "PHasMaskDelegate.h"

NS_ASSUME_NONNULL_BEGIN

typedef void (^VideoConsumerFPSBlock)(NSInteger videoFPS, NSInteger maskFPS);

@interface VideoConsumer : NSObject <PVideoWrapperDelegate, PHasMaskDelegate>

@property(nonatomic, strong) AppSinkGLView* appSinkGLView;
@property(nonatomic, copy, nullable) VideoConsumerFPSBlock onFPSUpdate;

-(id) init;

-(UIView*) makeRenderView: (RenderType) renderType frame:(CGRect) frame;

-(void) clean;

@end

NS_ASSUME_NONNULL_END
