//
//  main.m
//  core_ios
//
//  Created by Chamika Deshan on 9/9/20.
//


#import "AppDelegate.h"
#include "gst_ios_init.h"
#ifdef __OBJC__
#import <Foundation/Foundation.h>
#endif


int main(int argc, char * argv[]) {
    gst_ios_init();
    
    NSString * appDelegateClassName;
    @autoreleasepool {
        // Setup code that might create autoreleased objects goes here.
        appDelegateClassName = NSStringFromClass([AppDelegate class]);
    }
    return UIApplicationMain(argc, argv, nil, appDelegateClassName);
}
