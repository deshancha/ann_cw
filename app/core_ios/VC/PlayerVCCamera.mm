//
//  PlayerVC.m
//  core_ios
//
//  Created by Chamika Deshan on 9/9/20.
//

#include "AppLog.h"
#include "CoreWrapper.h"
#include "Defs.h"
#include "GSMain.h"
#import "MLContour.h"
#import "PWrapperDelegate.h"
#import "PlayerVC.h"
#import "VideoConsumer.h"
#include "VideoWrapper.h"

// ======= CONF ======

#define MAKE_CONF(X)                                                           \
  X = {                                                                        \
      .sendVideo = true,                                                       \
      .sendAudio = false,                                                      \
      .receiveAudio = false,                                                   \
      .receiveVideo = true,                                                    \
      .receiveRenderType = APPSINK_OPENGL,                                     \
      .senderRenderType = NONE,                                                \
      .useLowBandWidth = false,                                                \
  }

// using namespace AvatarIniOS::core;    // Not using AvatarIniOS::core here
using namespace AvatarIniOS::wrapper;
//---------------------------------------------------

typedef NS_ENUM(NSInteger, PipeLineType) {
  VIDEO_SENDER,
  VIDEO_RECEIVER
};

@interface PlayerVC () <PCoreWrapperDelegate> {
  CoreWrapper *coreWrapper;
  VideoWrapper *videoSenderWrapper;
  VideoWrapper *videoReceiverWrapper;

  Configuration conf;

  VideoConsumer *receiveVideoConsumer;
  VideoConsumer *selfVideoConsumer;

  NSDictionary *pipeLinePlist;

  CGPoint mCurrentAnchorPoint;

  VideoWrapper *rgbReceiver;
  MLContour *mlContour;
}

@property(weak, nonatomic) IBOutlet UIImageView *maskImage;
@property(weak, nonatomic) IBOutlet UIButton *stopBtn;
@property(weak, nonatomic) IBOutlet UISlider *shiftSlidebar;
@property(weak, nonatomic) IBOutlet UISlider *rotateSlidebar;
@property(weak, nonatomic) IBOutlet UILabel *maskPivotCurrentLbl;
@property(weak, nonatomic) IBOutlet UIView *anchotPanel;
@property(weak, nonatomic) IBOutlet UIImageView *anchorVisual;

@property(weak, nonatomic) IBOutlet UIButton *ltAnchorBtn;
@property(weak, nonatomic) IBOutlet UIButton *lbAnchoBtn;
@property(weak, nonatomic) IBOutlet UIButton *rtAnchorLbl;
@property(weak, nonatomic) IBOutlet UIButton *rbAnchorLbl;
@property(weak, nonatomic) IBOutlet UIButton *centerAnchotLbl;

@property(weak, nonatomic) IBOutlet UIButton *upAnchorBtn;
@property(weak, nonatomic) IBOutlet UIButton *downAnchorBtn;
@property(weak, nonatomic) IBOutlet UIButton *rightAnchorBtn;
@property(weak, nonatomic) IBOutlet UIButton *leftAnchorBtn;

@property(weak, nonatomic) IBOutlet UIImageView *maskView;

@end

@implementation PlayerVC

@synthesize isServer;
@synthesize ipAddress;
@synthesize stopBtn;

//---------------------------------------------------

- (NSString *)getPipeLine:(PipeLineType)pType
               renderType:(RenderType)rType
             lowBandWidth:(Boolean)lowbw {
  NSString *pipeLine;
  switch (pType) {
  case VIDEO_SENDER:
    pipeLine = [pipeLinePlist valueForKeyPath:@"PL_SENDER_VIDEO_NOSINK_T"];

    pipeLine = [NSString
        stringWithFormat:pipeLine,
                         isServer ? [pipeLinePlist
                                        valueForKeyPath:@"VIDEO_SEND_PORT"]
                                  : [pipeLinePlist
                                        valueForKeyPath:@"VIDEO_RECEIVE_PORT"],
                         ipAddress,
                         isServer
                             ? [pipeLinePlist
                                   valueForKeyPath:@"VIDEO_SEND_PORT_2"]
                             : [pipeLinePlist
                                   valueForKeyPath:@"VIDEO_RECEIVE_PORT_2"],
                         ipAddress];
    break;

  case VIDEO_RECEIVER:
    pipeLine = [pipeLinePlist valueForKeyPath:@"PL_RECEIVER_VIDEO_APPSINK"];

    pipeLine = [NSString
        stringWithFormat:pipeLine,
                         isServer ? [pipeLinePlist
                                        valueForKeyPath:@"VIDEO_RECEIVE_PORT"]
                                  : [pipeLinePlist
                                        valueForKeyPath:@"VIDEO_SEND_PORT"]];

    // To receive desktop capture
    // pipeLine = @"udpsrc port=1245 !
    // application/x-rtp,media=(string)video,encoding-name=(string)JPEG !
    // rtpjitterbuffer  !  rtpjpegdepay ! jpegdec  ! videoconvert !
    // video/x-raw,format=NV12 ! appsink name=sink sync=false";

    /** SENDER
        gst-launch-1.0 -v\
        rtpbin name=rtpbin \
        avfvideosrc capture-screen=true ! videoscale method=0 !
       video/x-raw,width=640,height=480 ! videoconvert ! video/x-raw,format=NV12
       ! jpegenc ! rtpjpegpay !  rtpbin.send_rtp_sink_0 \ rtpbin.send_rtp_src_0
       ! udpsink port=1245 host=192.168.1.4  sync=false
     */

    break;
  }

  return pipeLine;
}

- (void)viewDidAppear:(BOOL)animated {
  [super viewDidAppear:animated];

  // Create Video Consumer Views
  [self makeRenderViewForReceiver:conf.receiveRenderType
                           sender:conf.senderRenderType];

  pipeLinePlist =
      [NSDictionary dictionaryWithContentsOfFile:[[NSBundle mainBundle]
                                                     pathForResource:@"Pipeline"
                                                              ofType:@"plist"]];

  static TAG RGB_RECEIVER_TAG = "RGB_RECEIVER_TAG";

  NSString *rgbPipeline = [NSString
      stringWithFormat:[pipeLinePlist
                           valueForKeyPath:@"PL_RECEIVER_VIDEO_APPSINK_RGB"],
                       isServer ? [pipeLinePlist
                                      valueForKeyPath:@"VIDEO_RECEIVE_PORT_2"]
                                : [pipeLinePlist
                                      valueForKeyPath:@"VIDEO_SEND_PORT_2"]];

  rgbReceiver = new VideoWrapper(mlContour, RGB_RECEIVER_TAG, rgbPipeline,
                                 APPSINK_OPENGL, NULL);

  rgbReceiver->init();

  //--
  if (conf.sendVideo) {

    videoSenderWrapper = new VideoWrapper(
        selfVideoConsumer, V_SEND_TAG,
        [self getPipeLine:VIDEO_SENDER
               renderType:conf.senderRenderType
             lowBandWidth:conf.useLowBandWidth],
        conf.senderRenderType,
        NULL);
    videoSenderWrapper->init();
  }

  //--
  if (conf.receiveVideo) {
    videoReceiverWrapper = new VideoWrapper(
        receiveVideoConsumer, V_RECEV_TAG,
        [self getPipeLine:VIDEO_RECEIVER
               renderType:conf.receiveRenderType
             lowBandWidth:conf.useLowBandWidth],
        conf.receiveRenderType,
        NULL);
    videoReceiverWrapper->init();
  }



  pipeLinePlist = NULL;

  // GStreamer Main Loop
  coreWrapper->startMain();

  [_anchorVisual setCenter:_anchotPanel.center];
  mCurrentAnchorPoint = _anchotPanel.center;
}

//---------------------------------------------------

- (void)viewDidLoad {
  [super viewDidLoad];

  MAKE_CONF(conf);

  appLogger.enable(true);

  ipAddress = @"127.0.0.1";

  receiveVideoConsumer = [[VideoConsumer alloc] init];
  selfVideoConsumer = [[VideoConsumer alloc] init];
  mlContour = [[MLContour alloc] initWithDelegate:receiveVideoConsumer];

  mlContour.maskImageView = _maskView;

  videoSenderWrapper = NULL;
  videoReceiverWrapper = NULL;


  coreWrapper = new CoreWrapper(self);

  coreWrapper->initGStreamer();

  // playerWrap = new VideoWrapper(self);
  [stopBtn setEnabled:false];

  [self setupGestureControls];
}

- (void)dealloc {
  // etc
  delete coreWrapper;
  coreWrapper = NULL;

  delete videoSenderWrapper;
  delete videoReceiverWrapper;
  delete rgbReceiver;

  videoSenderWrapper = NULL;
  videoReceiverWrapper = NULL;
  rgbReceiver = NULL;

  [receiveVideoConsumer clean];
  [selfVideoConsumer clean];
}

//---------------------------------------------------

- (IBAction)btnPressed:(UIButton *)sender {

  if (sender == stopBtn) {
    if (self->videoSenderWrapper != NULL)
      self->videoSenderWrapper->stop();
    if (self->videoReceiverWrapper != NULL)
      self->videoReceiverWrapper->stop();

    if (self->rgbReceiver != NULL)
      self->rgbReceiver->stop();

    coreWrapper->stopAllPipeLines();
  }
}

//---------------------------------------------------

- (void)gstInitialized {
  dispatch_async(dispatch_get_main_queue(), ^{
    if (self->rgbReceiver != NULL)
      self->rgbReceiver->play();
    if (self->videoSenderWrapper != NULL)
      self->videoSenderWrapper->play();
    if (self->videoReceiverWrapper != NULL)
      self->videoReceiverWrapper->play();

  });
}



//---------------------------------------------------
// Other

- (void)makeRenderViewForReceiver:(RenderType)receiverRenderType
                           sender:(RenderType)senderRenderType {

  UIView *receiveVideoView =
      [receiveVideoConsumer makeRenderView:receiverRenderType
                                     frame:[self.videoContainerView frame]];
  if (!receiveVideoView) {
    NSLog(@"[ERROR] receiveVideoView is nil for renderType %ld", (long)receiverRenderType);
    return;
  }
  [[receiveVideoConsumer appSinkGLView] enableMask:YES];
  [self.videoContainerView addSubview:receiveVideoView];

  if (senderRenderType != NONE) {
    UIView *selfViewView =
        [selfVideoConsumer makeRenderView:senderRenderType
                                    frame:CGRectMake(0, 0, 320, 240)];
    if (selfViewView) {
      [self.videoContainerView addSubview:selfViewView];
    }
  }

  [receiveVideoView setTranslatesAutoresizingMaskIntoConstraints:NO];
  [self.videoContainerView
      addConstraints:
          [NSLayoutConstraint
              constraintsWithVisualFormat:@"H:|-0-[receiveVideoView]-0-|"
                                  options:
                                      NSLayoutFormatDirectionLeadingToTrailing
                                  metrics:nil
                                    views:NSDictionaryOfVariableBindings(
                                              receiveVideoView)]];
  [self.videoContainerView
      addConstraints:
          [NSLayoutConstraint
              constraintsWithVisualFormat:@"V:|-0-[receiveVideoView]-0-|"
                                  options:
                                      NSLayoutFormatDirectionLeadingToTrailing
                                  metrics:nil
                                    views:NSDictionaryOfVariableBindings(
                                              receiveVideoView)]];
}

- (IBAction)sliderValueChanged:(UISlider *)sender {
  if (sender == _shiftSlidebar) {
    [[receiveVideoConsumer appSinkGLView] setShift:sender.value];
  } else if (sender == _rotateSlidebar) {
    [[receiveVideoConsumer appSinkGLView] setRotate:sender.value];
  }
}

- (IBAction)btnShowHideMask:(id)sender {
  [_maskImage setHidden:!_maskImage.isHidden];
}

- (IBAction)mask3DEnable:(UISwitch *)sender {
  [[receiveVideoConsumer appSinkGLView] enableMask:[sender isOn]];
}

- (IBAction)depthPopupShift:(id)sender {
  [[receiveVideoConsumer appSinkGLView] depthPopShift];
}

- (IBAction)anchotShowHideBtn:(id)sender {
  [_anchotPanel setHidden:!_anchotPanel.isHidden];
}

- (IBAction)anchotSelectBtn:(UIButton *)sender {

  [_maskPivotCurrentLbl setText:[sender currentTitle]];

  if (sender == _upAnchorBtn) {
    mCurrentAnchorPoint.y -= 20;
    [self updateMaskPivot];
  } else if (sender == _downAnchorBtn) {
    mCurrentAnchorPoint.y += 20;
    [self updateMaskPivot];
  } else if (sender == _rightAnchorBtn) {
    mCurrentAnchorPoint.x += 20;
    [self updateMaskPivot];
  } else if (sender == _leftAnchorBtn) {
    mCurrentAnchorPoint.x -= 20;
    [self updateMaskPivot];
  }
}

- (IBAction)changeBackground:(id)sender {
  [[receiveVideoConsumer appSinkGLView] nextBackground];
}

- (IBAction)closeAnchorView:(id)sender {
}

#pragma mark - Gestures

//-------------------------------------------------------------------------------------------

- (void)setupGestureControls {

  UITapGestureRecognizer *singleTapGesture = [[UITapGestureRecognizer alloc]
      initWithTarget:self
              action:@selector(singleTapGestureCallback:)];

  singleTapGesture.numberOfTapsRequired = 1;

  UITapGestureRecognizer *doubleTapGesture = [[UITapGestureRecognizer alloc]
      initWithTarget:self
              action:@selector(doubleTapGestureCallback:)];

  doubleTapGesture.numberOfTapsRequired = 2;

  [singleTapGesture requireGestureRecognizerToFail:doubleTapGesture];

  [_anchotPanel addGestureRecognizer:singleTapGesture];
  [_anchotPanel addGestureRecognizer:doubleTapGesture];
}

//-------------------------------------------------------------------------------------------

- (void)singleTapGestureCallback:(UITapGestureRecognizer *)tapRecognizer {
  mCurrentAnchorPoint = [tapRecognizer locationInView:tapRecognizer.view];
  [self updateMaskPivot];
}

//-------------------------------------------------------------------------------------------

- (void)updateMaskPivot {
  [_anchorVisual setCenter:mCurrentAnchorPoint];

  CGSize size = _anchotPanel.bounds.size;

  CGPoint normalizedPoint =
      CGPointMake((size.width - mCurrentAnchorPoint.x) / size.width,
                  (size.height - mCurrentAnchorPoint.y) / size.height);

  NSLog(@"Point - %f, %f", normalizedPoint.x, normalizedPoint.y);

  [[receiveVideoConsumer appSinkGLView] setMaskPivotX:normalizedPoint.x
                                               pivotY:normalizedPoint.y];
}

//-------------------------------------------------------------------------------------------

// double tapon image view
- (void)doubleTapGestureCallback:(UITapGestureRecognizer *)tapRecognizer {
}

@end
