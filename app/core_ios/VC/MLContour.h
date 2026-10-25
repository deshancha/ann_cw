//
//  VideoConsumerContour.h
//  Call-App
//
//  Created by Chamika Deshan on 2/9/22.
//

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#import "PWrapperDelegate.h"
#import "PHasMaskDelegate.h"
#import "CoreMLSegmenter.h"

NS_ASSUME_NONNULL_BEGIN

@interface MLContour : NSObject <PVideoWrapperDelegate>
{
    id <PHasMaskDelegate> delegate;
    CoreMLSegmenter *segmenter;
}

@property(nonatomic, strong) UIImageView* maskImageView;

-(id) init:(NSString*)modelName delegate:(id <PHasMaskDelegate>)maskDelegate;

-(id) initWithDelegate:(id <PHasMaskDelegate>)maskDelegate;

-(void) clear;

@end

NS_ASSUME_NONNULL_END
