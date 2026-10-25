//
//  PlayerVC.h
//  core_ios
//
//  Created by Chamika Deshan on 9/9/20.
//

#import <UIKit/UIKit.h>
#import "AppSinkGLView.h"

NS_ASSUME_NONNULL_BEGIN

@interface PlayerVC : UIViewController

@property (weak, nonatomic) IBOutlet UIView *videoContainerView;

@property(nonatomic, strong) NSString* ipAddress;
@property (nonatomic, assign) BOOL isServer;

@end

NS_ASSUME_NONNULL_END
