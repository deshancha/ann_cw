//
//  PWrapperDelegate.h
//  Basic
//
//  Created by Chamika Deshan on 8/23/20.
//

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>

NS_ASSUME_NONNULL_BEGIN

@protocol PHasMaskDelegate <NSObject>

-(void) hasMask:(CVPixelBufferRef)maskRef;

@end

NS_ASSUME_NONNULL_END
