

#import "AppSinkGLView.h"
#import <QuartzCore/QuartzCore.h>
#import <AVFoundation/AVUtilities.h>
#import <mach/mach_time.h>

#import <OpenGLES/ES3/gl.h>
#import <OpenGLES/ES3/glext.h>

#define GL_RED_EXT GL_RED
#define GL_RG_EXT GL_RG

// Uniform index.
enum
{
    UNIFORM_RGB,
    UNIFORM_Y,
    UNIFORM_UV,
    UNIFORM_COLOR_CONVERSION_MATRIX,
    UNIFORM_SHIFT,
    UNIFORM_ANGLE,
    UNIFORM_ENABLEMASK,
    UNIFORM_MASKPIVOT_X,
    UNIFORM_MASKPIVOT_Y,
    SHIFT_X_OFFSET,
    BACKGROUND,
    NUM_UNIFORMS
};
GLint uniforms[NUM_UNIFORMS];

// Attribute index.
enum
{
    ATTRIB_VERTEX,
    ATTRIB_TEXCOORD,
    NUM_ATTRIBUTES
};

static const GLfloat kColorConversion601[] = {
        1.164,  1.164, 1.164,
          0.0, -0.392, 2.017,
        1.596, -0.813,   0.0,
};

// BT.709, which is the standard for HDTV.
static const GLfloat kColorConversion709[] = {
        1.164,  1.164, 1.164,
          0.0, -0.213, 2.112,
        1.793, -0.533,   0.0,
};

@interface AppSinkGLView ()
{
    // The pixel dimensions of the CAEAGLLayer.
    GLint _backingWidth;
    GLint _backingHeight;

    CVOpenGLESTextureRef _rgbTexture;
    
    EAGLContext *_context;
    CVOpenGLESTextureRef _lumaTexture;
    CVOpenGLESTextureRef _chromaTexture;
    CVOpenGLESTextureCacheRef _videoTextureCache;
    CVOpenGLESTextureCacheRef _videoTextureCache2;
    
    GLuint _frameBufferHandle;
    GLuint _colorBufferHandle;
    
    const GLfloat *_preferredConversion;
    
    float shiftValue;
    float angleValue;
    float enableMask;
    float maskPivotX;
    float maskPivotY;
    bool enableStartingXoffset;
    int background;
    
    CVPixelBufferRef pixelBuffer2;
    GLuint _maskGLTexture;
}

@property GLuint program;

- (void)setupBuffers;
- (void)cleanUpTextures;

- (BOOL)loadShaders;
- (BOOL)compileShader:(GLuint *)shader type:(GLenum)type URL:(NSURL *)URL;
- (BOOL)linkProgram:(GLuint)prog;
- (BOOL)validateProgram:(GLuint)prog;

@end

@implementation AppSinkGLView

//------------------------------------------------------

+ (Class)layerClass
{
    return [CAEAGLLayer class];
}

//------------------------------------------------------

- (id)initWithCoder:(NSCoder *)aDecoder
{
    if ((self = [super initWithCoder:aDecoder]))
    {
        if(![self initContext])
        return nil;
    }
    
    return self;
}

//------------------------------------------------------

- (id)initWithFrame:(CGRect)rect
{
    if ((self = [super initWithFrame:rect]))
    {
        if(![self initContext])
            return nil;
    }
        
    return self;
}

//------------------------------------------------------

- (void) setShift:(float) val {
    shiftValue = val;
}

//------------------------------------------------------

- (void) setRotate:(float) val {
    angleValue = val;
}

//------------------------------------------------------

- (void) enableMask:(BOOL) val {
    enableMask = val? 1.1 : 0.0;
}

//------------------------------------------------------

- (void) setMaskPivotX:(float) x pivotY:(float) y {
    maskPivotX = x;
    maskPivotY = y;
}

//------------------------------------------------------

- (void) depthPopShift {
    enableStartingXoffset = !enableStartingXoffset;
}

- (void) nextBackground {
    background  = ++background > 4 ? 0 : background;
}

//------------------------------------------------------

- (Boolean) initContext {
    
    _rgbTexture = NULL;
    _lumaTexture = NULL;
    _chromaTexture = NULL;
    
    // Use 2x scale factor on Retina displays.
    self.contentScaleFactor = [[UIScreen mainScreen] scale];

    // Get and configure the layer.
    CAEAGLLayer *eaglLayer = (CAEAGLLayer *)self.layer;

    eaglLayer.opaque = TRUE;
    eaglLayer.drawableProperties = @{ kEAGLDrawablePropertyRetainedBacking :[NSNumber numberWithBool:NO],
                                      kEAGLDrawablePropertyColorFormat : kEAGLColorFormatRGBA8};

    // Set the context into which the frames will be drawn.
    _context = [[EAGLContext alloc] initWithAPI:kEAGLRenderingAPIOpenGLES2];

    if (!_context || ![EAGLContext setCurrentContext:_context] || ![self loadShaders]) {
        return false;
    }
    
    // Set the default conversion to BT.709, which is the standard for HDTV.
    _preferredConversion = kColorConversion709;
    
    UIImage* alphaImage = [UIImage imageNamed:@"human"];
    
    pixelBuffer2 = [AppSinkGLView pixelBufferFromImage:alphaImage.CGImage];
    
    return true;
}

//------------------------------------------------------

# pragma mark - OpenGL setup

- (void)setupGL
{
    [EAGLContext setCurrentContext:_context];
    [self setupBuffers];
    [self loadShaders];
    
    glUseProgram(self.program);
    
    
    glUniform1i(uniforms[UNIFORM_Y], 0);
    glUniform1i(uniforms[UNIFORM_UV], 1);
    glUniform1i(uniforms[UNIFORM_RGB], 2);
    enableMask = 1.1f;
    background = 3;
    glUniform1f(uniforms[UNIFORM_SHIFT], 0.0f);
    glUniform1f(uniforms[UNIFORM_ANGLE], 0.0f);
    glUniform1f(uniforms[UNIFORM_ENABLEMASK], enableMask);
    glUniform1f(uniforms[UNIFORM_MASKPIVOT_X], 0.5f);
    glUniform1f(uniforms[UNIFORM_MASKPIVOT_Y], 0.5f);
    glUniform1f(uniforms[SHIFT_X_OFFSET], enableStartingXoffset ? 1.0 : 0.0);
    glUniform1i(uniforms[BACKGROUND], background);
    
    
    // Create CVOpenGLESTextureCacheRef for optimal CVPixelBufferRef to GLES texture conversion.
    if (!_videoTextureCache) {
        CVReturn err = CVOpenGLESTextureCacheCreate(kCFAllocatorDefault, NULL, _context, NULL, &_videoTextureCache);
        if (err != noErr) {
            NSLog(@"Error at CVOpenGLESTextureCacheCreate %d", err);
            return;
        }
    }
    
    if (!_videoTextureCache2) {
        CVReturn err = CVOpenGLESTextureCacheCreate(kCFAllocatorDefault, NULL, _context, NULL, &_videoTextureCache2);
        if (err != noErr) {
            NSLog(@"Error at CVOpenGLESTextureCacheCreate %d", err);
            return;
        }
    }
    
    
}

//------------------------------------------------------

#pragma mark - Utilities

- (void)setupBuffers
{
    glDisable(GL_DEPTH_TEST);
    
    CGFloat screenScale = [UIScreen mainScreen].scale;
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT16, CGRectGetWidth(self.bounds) * screenScale, CGRectGetHeight(self.bounds) * screenScale);
    
    glEnableVertexAttribArray(ATTRIB_VERTEX);
    glVertexAttribPointer(ATTRIB_VERTEX, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), 0);
    
    glEnableVertexAttribArray(ATTRIB_TEXCOORD);
    glVertexAttribPointer(ATTRIB_TEXCOORD, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), 0);
    
    glGenFramebuffers(1, &_frameBufferHandle);
    glBindFramebuffer(GL_FRAMEBUFFER, _frameBufferHandle);
    
    glGenRenderbuffers(1, &_colorBufferHandle);
    glBindRenderbuffer(GL_RENDERBUFFER, _colorBufferHandle);
    
    [_context renderbufferStorage:GL_RENDERBUFFER fromDrawable:(CAEAGLLayer *)self.layer];
    glGetRenderbufferParameteriv(GL_RENDERBUFFER, GL_RENDERBUFFER_WIDTH, &_backingWidth);
    glGetRenderbufferParameteriv(GL_RENDERBUFFER, GL_RENDERBUFFER_HEIGHT, &_backingHeight);

    glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, _colorBufferHandle);
    if (glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE) {
        NSLog(@"Failed to make complete framebuffer object %x", glCheckFramebufferStatus(GL_FRAMEBUFFER));
    }
}

//------------------------------------------------------

- (void)cleanUpTextures
{
    if (_lumaTexture) {
        CFRelease(_lumaTexture);
        _lumaTexture = NULL;
    }
    
    if (_chromaTexture) {
        CFRelease(_chromaTexture);
        _chromaTexture = NULL;
    }
    
    if (_rgbTexture) {
        CFRelease(_rgbTexture);
        _rgbTexture = NULL;
    }
    
    // Periodic texture cache flush every frame
    CVOpenGLESTextureCacheFlush(_videoTextureCache, 0);
    CVOpenGLESTextureCacheFlush(_videoTextureCache2, 0);
}

- (void)dealloc
{
    [self cleanUpTextures];
    
    if(_videoTextureCache) {
        CFRelease(_videoTextureCache);
    }
    
    if(_videoTextureCache2) {
        CFRelease(_videoTextureCache2);
    }
    
    if (_maskGLTexture) {
        glDeleteTextures(1, &_maskGLTexture);
        _maskGLTexture = 0;
    }
}

#pragma mark - OpenGLES drawing

- (void)displayPixelBuffer:(CVPixelBufferRef)pixelBuffer
{
    CVReturn err;
    if (pixelBuffer != NULL) {
        // Video Texture
        {
            int frameWidth = CVPixelBufferGetWidth(pixelBuffer);
            int frameHeight = CVPixelBufferGetHeight(pixelBuffer);
            
            if (!_videoTextureCache) {
                NSLog(@"No video texture cache");
                return;
            }
            
            [self cleanUpTextures];
            
            CFTypeRef colorAttachments = CVBufferGetAttachment(pixelBuffer, kCVImageBufferYCbCrMatrixKey, NULL);
            
            if (colorAttachments == kCVImageBufferYCbCrMatrix_ITU_R_601_4) {
                _preferredConversion = kColorConversion601;
            }
            else {
                _preferredConversion = kColorConversion709;
            }
            
            /*
             CVOpenGLESTextureCacheCreateTextureFromImage will create GLES texture optimally from CVPixelBufferRef.
             */
            
            /*
            Create Y and UV textures from the pixel buffer. These textures will be drawn on the frame buffer Y-plane.
            */
            glActiveTexture(GL_TEXTURE0);
            err = CVOpenGLESTextureCacheCreateTextureFromImage(kCFAllocatorDefault,
                                                               _videoTextureCache,
                                                               pixelBuffer,
                                                               NULL,
                                                               GL_TEXTURE_2D,
                                                               GL_RED_EXT,
                                                               frameWidth,
                                                               frameHeight,
                                                               GL_RED_EXT,
                                                               GL_UNSIGNED_BYTE,
                                                               0,
                                                               &_lumaTexture);
            if (err) {
                NSLog(@"Error at CVOpenGLESTextureCacheCreateTextureFromImage luma %d", err);
            }
            
            glBindTexture(CVOpenGLESTextureGetTarget(_lumaTexture), CVOpenGLESTextureGetName(_lumaTexture));
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
            
            // UV-plane.
            glActiveTexture(GL_TEXTURE1);
            err = CVOpenGLESTextureCacheCreateTextureFromImage(kCFAllocatorDefault,
                                                               _videoTextureCache,
                                                               pixelBuffer,
                                                               NULL,
                                                               GL_TEXTURE_2D,
                                                               GL_RG_EXT,
                                                               frameWidth / 2,
                                                               frameHeight / 2,
                                                               GL_RG_EXT,
                                                               GL_UNSIGNED_BYTE,
                                                               1,
                                                               &_chromaTexture);
            if (err) {
                NSLog(@"Error at CVOpenGLESTextureCacheCreateTextureFromImage chroma %d", err);
            }
            
            glBindTexture(CVOpenGLESTextureGetTarget(_chromaTexture), CVOpenGLESTextureGetName(_chromaTexture));
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        }
        
        if (pixelBuffer2 != NULL && enableMask > 1.f)
        {
            int frameWidth = (int) CVPixelBufferGetWidth(pixelBuffer2);
            int frameHeight = (int) CVPixelBufferGetHeight(pixelBuffer2);
            
            if (!_videoTextureCache2) {
                NSLog(@"No video texture cache");
                return;
            }
            
            /*
             CVOpenGLESTextureCacheCreateTextureFromImage will create GLES texture optimally from CVPixelBufferRef.
             */
            
            /*
             Create RGB textures from the pixel buffer. These textures will be drawn on the frame buffer Y-plane.
             */
            glActiveTexture(GL_TEXTURE2);
            err = CVOpenGLESTextureCacheCreateTextureFromImage(kCFAllocatorDefault,
                                                               _videoTextureCache2,
                                                               pixelBuffer2,
                                                               NULL,
                                                               GL_TEXTURE_2D,
                                                               GL_RGBA,
                                                               frameWidth,
                                                               frameHeight,
                                                               GL_RGBA,
                                                               GL_UNSIGNED_BYTE,
                                                               0,
                                                               &_rgbTexture);
            if (err) {
                NSLog(@"Error at CVOpenGLESTextureCacheCreateTextureFromImage rgb%d", err);
            }
            
            glBindTexture(CVOpenGLESTextureGetTarget(_rgbTexture), CVOpenGLESTextureGetName(_rgbTexture));
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        }
        
        glBindFramebuffer(GL_FRAMEBUFFER, _frameBufferHandle);
        
        // Set the view port to the entire view.
        glViewport(0, 0, _backingWidth, _backingHeight);
        
        CFRelease(pixelBuffer);
    }
    
        
    
    glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
    
    // Use shader program.
    glUseProgram(self.program);
    
    glUniformMatrix3fv(uniforms[UNIFORM_COLOR_CONVERSION_MATRIX], 1, GL_FALSE, _preferredConversion);
    glUniform1f(uniforms[UNIFORM_SHIFT], shiftValue);
    glUniform1f(uniforms[UNIFORM_ANGLE], angleValue);
    glUniform1f(uniforms[UNIFORM_ENABLEMASK], enableMask);
    glUniform1f(uniforms[UNIFORM_MASKPIVOT_X], maskPivotX);
    glUniform1f(uniforms[UNIFORM_MASKPIVOT_Y], maskPivotY);
    glUniform1f(uniforms[SHIFT_X_OFFSET], enableStartingXoffset ? 1.0 : 0.0);
    glUniform1i(uniforms[BACKGROUND], background);
    
    // Set up the quad vertices with respect to the orientation and aspect ratio of the video.
    CGRect vertexSamplingRect = AVMakeRectWithAspectRatioInsideRect(self.presentationRect, self.layer.bounds);
    
    // Compute normalized quad coordinates to draw the frame into.
    CGSize normalizedSamplingSize = CGSizeMake(0.0, 0.0);
    CGSize cropScaleAmount = CGSizeMake(vertexSamplingRect.size.width/self.layer.bounds.size.width, vertexSamplingRect.size.height/self.layer.bounds.size.height);
    
    // Normalize the quad vertices.
    if (cropScaleAmount.width > cropScaleAmount.height) {
        normalizedSamplingSize.width = 1.0;
        normalizedSamplingSize.height = cropScaleAmount.height/cropScaleAmount.width;
    }
    else {
        normalizedSamplingSize.width = 1.0;
        normalizedSamplingSize.height = cropScaleAmount.width/cropScaleAmount.height;
    }
    
    /*
     The quad vertex data defines the region of 2D plane onto which we draw our pixel buffers.
     Vertex data formed using (-1,-1) and (1,1) as the bottom left and top right coordinates respectively, covers the entire screen.
     */
    GLfloat quadVertexData [] = {
        -1 * normalizedSamplingSize.width, -1 * normalizedSamplingSize.height,
             normalizedSamplingSize.width, -1 * normalizedSamplingSize.height,
        -1 * normalizedSamplingSize.width, normalizedSamplingSize.height,
             normalizedSamplingSize.width, normalizedSamplingSize.height,
    };
    
    // Update attribute values.
    glVertexAttribPointer(ATTRIB_VERTEX, 2, GL_FLOAT, 0, 0, quadVertexData);
    glEnableVertexAttribArray(ATTRIB_VERTEX);

    /*
     The texture vertices are set up such that we flip the texture vertically. This is so that our top left origin buffers match OpenGL's bottom left texture coordinate system.
     */
    CGRect textureSamplingRect = CGRectMake(0, 0, 1, 1);
    GLfloat quadTextureData[] =  {
        CGRectGetMinX(textureSamplingRect), CGRectGetMaxY(textureSamplingRect),
        CGRectGetMaxX(textureSamplingRect), CGRectGetMaxY(textureSamplingRect),
        CGRectGetMinX(textureSamplingRect), CGRectGetMinY(textureSamplingRect),
        CGRectGetMaxX(textureSamplingRect), CGRectGetMinY(textureSamplingRect)
    };
    
    glVertexAttribPointer(ATTRIB_TEXCOORD, 2, GL_FLOAT, 0, 0, quadTextureData);
    glEnableVertexAttribArray(ATTRIB_TEXCOORD);
    
    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);

    glBindRenderbuffer(GL_RENDERBUFFER, _colorBufferHandle);
    [_context presentRenderbuffer:GL_RENDERBUFFER];
}

//------------------------------------------------------

- (void)displayPixelBuffer:(CVPixelBufferRef)pixelBuffer mask:(CVPixelBufferRef)mask {
    CVReturn err;
    if (pixelBuffer != NULL) {
        // Video Texture
        {
            int frameWidth = CVPixelBufferGetWidth(pixelBuffer);
            int frameHeight = CVPixelBufferGetHeight(pixelBuffer);
            
            if (!_videoTextureCache) {
                NSLog(@"No video texture cache");
                return;
            }
            
            [self cleanUpTextures];
            
            CFTypeRef colorAttachments = CVBufferGetAttachment(pixelBuffer, kCVImageBufferYCbCrMatrixKey, NULL);
            
            if (colorAttachments == kCVImageBufferYCbCrMatrix_ITU_R_601_4) {
                _preferredConversion = kColorConversion601;
            }
            else {
                _preferredConversion = kColorConversion709;
            }
            
            /*
             CVOpenGLESTextureCacheCreateTextureFromImage will create GLES texture optimally from CVPixelBufferRef.
             */
            
            /*
            Create Y and UV textures from the pixel buffer. These textures will be drawn on the frame buffer Y-plane.
            */
            glActiveTexture(GL_TEXTURE0);
            err = CVOpenGLESTextureCacheCreateTextureFromImage(kCFAllocatorDefault,
                                                               _videoTextureCache,
                                                               pixelBuffer,
                                                               NULL,
                                                               GL_TEXTURE_2D,
                                                               GL_RED_EXT,
                                                               frameWidth,
                                                               frameHeight,
                                                               GL_RED_EXT,
                                                               GL_UNSIGNED_BYTE,
                                                               0,
                                                               &_lumaTexture);
            if (err) {
                NSLog(@"Error at CVOpenGLESTextureCacheCreateTextureFromImage luma %d", err);
            }
            
            glBindTexture(CVOpenGLESTextureGetTarget(_lumaTexture), CVOpenGLESTextureGetName(_lumaTexture));
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
            
            // UV-plane.
            glActiveTexture(GL_TEXTURE1);
            err = CVOpenGLESTextureCacheCreateTextureFromImage(kCFAllocatorDefault,
                                                               _videoTextureCache,
                                                               pixelBuffer,
                                                               NULL,
                                                               GL_TEXTURE_2D,
                                                               GL_RG_EXT,
                                                               frameWidth / 2,
                                                               frameHeight / 2,
                                                               GL_RG_EXT,
                                                               GL_UNSIGNED_BYTE,
                                                               1,
                                                               &_chromaTexture);
            if (err) {
                NSLog(@"Error at CVOpenGLESTextureCacheCreateTextureFromImage chroma %d", err);
            }
            
            glBindTexture(CVOpenGLESTextureGetTarget(_chromaTexture), CVOpenGLESTextureGetName(_chromaTexture));
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        }
        
        if (mask != NULL)
        {
            size_t frameWidth = CVPixelBufferGetWidth(mask);
            size_t frameHeight = CVPixelBufferGetHeight(mask);
            size_t bytesPerRow = CVPixelBufferGetBytesPerRow(mask);
            
            if (_maskGLTexture == 0) {
                glGenTextures(1, &_maskGLTexture);
            }
            
            glActiveTexture(GL_TEXTURE2);
            glBindTexture(GL_TEXTURE_2D, _maskGLTexture);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
            
            CVReturn lockStatus = CVPixelBufferLockBaseAddress(mask, kCVPixelBufferLock_ReadOnly);
            if (lockStatus == kCVReturnSuccess) {
                const uint8_t *base = (const uint8_t *)CVPixelBufferGetBaseAddress(mask);
                if (bytesPerRow == frameWidth) {
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, (GLsizei)frameWidth, (GLsizei)frameHeight, 0, GL_LUMINANCE, GL_UNSIGNED_BYTE, base);
                } else {
                    // Stride safe unpack: remove row padding (ex: 256 bytesPerRow for 224 width)
                    uint8_t *packed = (uint8_t *)malloc(frameWidth * frameHeight);
                    if (packed) {
                        for (size_t r = 0; r < frameHeight; r++) {
                            memcpy(packed + r * frameWidth, base + r * bytesPerRow, frameWidth);
                        }
                        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, (GLsizei)frameWidth, (GLsizei)frameHeight, 0, GL_LUMINANCE, GL_UNSIGNED_BYTE, packed);
                        free(packed);
                    }
                }
                CVPixelBufferUnlockBaseAddress(mask, kCVPixelBufferLock_ReadOnly);
            }
        }
        
        glBindFramebuffer(GL_FRAMEBUFFER, _frameBufferHandle);
        
        // Set the view port to the entire view.
        glViewport(0, 0, _backingWidth, _backingHeight);
        
        CFRelease(pixelBuffer);
    }
    
    glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
    
    // Use shader program.
    glUseProgram(self.program);
    
    // Explicitly bind samplers to corresponding texture units
    glUniform1i(uniforms[UNIFORM_Y], 0);
    glUniform1i(uniforms[UNIFORM_UV], 1);
    glUniform1i(uniforms[UNIFORM_RGB], 2);
    
    glUniformMatrix3fv(uniforms[UNIFORM_COLOR_CONVERSION_MATRIX], 1, GL_FALSE, _preferredConversion);
    glUniform1f(uniforms[UNIFORM_SHIFT], shiftValue);
    glUniform1f(uniforms[UNIFORM_ANGLE], angleValue);
    glUniform1f(uniforms[UNIFORM_ENABLEMASK], enableMask);
    glUniform1f(uniforms[UNIFORM_MASKPIVOT_X], maskPivotX);
    glUniform1f(uniforms[UNIFORM_MASKPIVOT_Y], maskPivotY);
    glUniform1f(uniforms[SHIFT_X_OFFSET], enableStartingXoffset ? 1.0 : 0.0);
    glUniform1i(uniforms[BACKGROUND], background);
    
    // Ensure all 3 texture units are bound to their respective textures
    glActiveTexture(GL_TEXTURE0);
    if (_lumaTexture) {
        glBindTexture(CVOpenGLESTextureGetTarget(_lumaTexture), CVOpenGLESTextureGetName(_lumaTexture));
    }
    glActiveTexture(GL_TEXTURE1);
    if (_chromaTexture) {
        glBindTexture(CVOpenGLESTextureGetTarget(_chromaTexture), CVOpenGLESTextureGetName(_chromaTexture));
    }
    glActiveTexture(GL_TEXTURE2);
    if (_maskGLTexture) {
        glBindTexture(GL_TEXTURE_2D, _maskGLTexture);
    }
    
    
    // Set up the quad vertices with respect to the orientation and aspect ratio of the video.
    CGRect vertexSamplingRect = AVMakeRectWithAspectRatioInsideRect(self.presentationRect, self.layer.bounds);
    
    // Compute normalized quad coordinates to draw the frame into.
    CGSize normalizedSamplingSize = CGSizeMake(0.0, 0.0);
    CGSize cropScaleAmount = CGSizeMake(vertexSamplingRect.size.width/self.layer.bounds.size.width, vertexSamplingRect.size.height/self.layer.bounds.size.height);
    
    // Normalize the quad vertices.
    if (cropScaleAmount.width > cropScaleAmount.height) {
        normalizedSamplingSize.width = 1.0;
        normalizedSamplingSize.height = cropScaleAmount.height/cropScaleAmount.width;
    }
    else {
        normalizedSamplingSize.width = 1.0;
        normalizedSamplingSize.height = cropScaleAmount.width/cropScaleAmount.height;
    }
    
    /*
     The quad vertex data defines the region of 2D plane onto which we draw our pixel buffers.
     Vertex data formed using (-1,-1) and (1,1) as the bottom left and top right coordinates respectively, covers the entire screen.
     */
    GLfloat quadVertexData [] = {
        -1 * normalizedSamplingSize.width, -1 * normalizedSamplingSize.height,
             normalizedSamplingSize.width, -1 * normalizedSamplingSize.height,
        -1 * normalizedSamplingSize.width, normalizedSamplingSize.height,
             normalizedSamplingSize.width, normalizedSamplingSize.height,
    };
    
    // Update attribute values.
    glVertexAttribPointer(ATTRIB_VERTEX, 2, GL_FLOAT, 0, 0, quadVertexData);
    glEnableVertexAttribArray(ATTRIB_VERTEX);

    /*
     The texture vertices are set up such that we flip the texture vertically. This is so that our top left origin buffers match OpenGL's bottom left texture coordinate system.
     */
    CGRect textureSamplingRect = CGRectMake(0, 0, 1, 1);
    GLfloat quadTextureData[] =  {
        CGRectGetMinX(textureSamplingRect), CGRectGetMaxY(textureSamplingRect),
        CGRectGetMaxX(textureSamplingRect), CGRectGetMaxY(textureSamplingRect),
        CGRectGetMinX(textureSamplingRect), CGRectGetMinY(textureSamplingRect),
        CGRectGetMaxX(textureSamplingRect), CGRectGetMinY(textureSamplingRect)
    };
    
    glVertexAttribPointer(ATTRIB_TEXCOORD, 2, GL_FLOAT, 0, 0, quadTextureData);
    glEnableVertexAttribArray(ATTRIB_TEXCOORD);
    
    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);

    glBindRenderbuffer(GL_RENDERBUFFER, _colorBufferHandle);
    [_context presentRenderbuffer:GL_RENDERBUFFER];
}

//------------------------------------------------------


#pragma mark -  OpenGL ES 2 shader compilation

- (BOOL)loadShaders
{
    GLuint vertShader, fragShader;
    NSURL *vertShaderURL, *fragShaderURL;
    
    // Create the shader program.
    self.program = glCreateProgram();
    
    NSBundle *bundle = [NSBundle bundleForClass:[self class]];
    
    // Create and compile the vertex shader.
    vertShaderURL = [bundle URLForResource:@"Shader" withExtension:@"vsh"];
    
    if (![self compileShader:&vertShader type:GL_VERTEX_SHADER URL:vertShaderURL]) {
        NSLog(@"Failed to compile vertex shader");
        return NO;
    }
    
    // Create and compile fragment shader.
    fragShaderURL = [bundle URLForResource:@"Shader" withExtension:@"fsh"];
    
    if (![self compileShader:&fragShader type:GL_FRAGMENT_SHADER URL:fragShaderURL]) {
        NSLog(@"Failed to compile fragment shader");
        return NO;
    }
    
    // Attach vertex shader to program.
    glAttachShader(self.program, vertShader);
    
    // Attach fragment shader to program.
    glAttachShader(self.program, fragShader);
    
    // Bind attribute locations. This needs to be done prior to linking.
    glBindAttribLocation(self.program, ATTRIB_VERTEX, "position");
    glBindAttribLocation(self.program, ATTRIB_TEXCOORD, "texCoord");
    
    // Link the program.
    if (![self linkProgram:self.program]) {
        NSLog(@"Failed to link program: %d", self.program);
        
        if (vertShader) {
            glDeleteShader(vertShader);
            vertShader = 0;
        }
        if (fragShader) {
            glDeleteShader(fragShader);
            fragShader = 0;
        }
        if (self.program) {
            glDeleteProgram(self.program);
            self.program = 0;
        }
        
        return NO;
    }
    
    // Get uniform locations.
    uniforms[UNIFORM_Y] = glGetUniformLocation(self.program, "SamplerY");
    uniforms[UNIFORM_UV] = glGetUniformLocation(self.program, "SamplerUV");
    uniforms[UNIFORM_RGB] = glGetUniformLocation(self.program, "SamplerTextureMask");
    uniforms[UNIFORM_COLOR_CONVERSION_MATRIX] = glGetUniformLocation(self.program, "colorConversionMatrix");
    uniforms[UNIFORM_SHIFT] = glGetUniformLocation(self.program, "shiftVal");
    uniforms[UNIFORM_ANGLE] = glGetUniformLocation(self.program, "angleInDegrees");
    uniforms[UNIFORM_ENABLEMASK] = glGetUniformLocation(self.program, "enableMask");
    uniforms[UNIFORM_MASKPIVOT_X] = glGetUniformLocation(self.program, "maskPivotX");
    uniforms[UNIFORM_MASKPIVOT_Y] = glGetUniformLocation(self.program, "maskPivotY");
    uniforms[SHIFT_X_OFFSET] = glGetUniformLocation(self.program, "startingXOffset");
    uniforms[BACKGROUND] = glGetUniformLocation(self.program, "background");
    
    
    // Release vertex and fragment shaders.
    if (vertShader) {
        glDetachShader(self.program, vertShader);
        glDeleteShader(vertShader);
    }
    if (fragShader) {
        glDetachShader(self.program, fragShader);
        glDeleteShader(fragShader);
    }
    
    return YES;
}

//------------------------------------------------------

- (BOOL)compileShader:(GLuint *)shader type:(GLenum)type URL:(NSURL *)URL
{
    NSError *error;
    NSString *sourceString = [[NSString alloc] initWithContentsOfURL:URL encoding:NSUTF8StringEncoding error:&error];
    if (sourceString == nil) {
        NSLog(@"Failed to load vertex shader: %@", [error localizedDescription]);
        return NO;
    }
    
    GLint status;
    const GLchar *source;
    source = (GLchar *)[sourceString UTF8String];
    
    *shader = glCreateShader(type);
    glShaderSource(*shader, 1, &source, NULL);
    glCompileShader(*shader);
    
#if defined(DEBUG)
    GLint logLength;
    glGetShaderiv(*shader, GL_INFO_LOG_LENGTH, &logLength);
    if (logLength > 0) {
        GLchar *log = (GLchar *)malloc(logLength);
        glGetShaderInfoLog(*shader, logLength, &logLength, log);
        NSLog(@"Shader compile log:\n%s", log);
        free(log);
    }
#endif
    
    glGetShaderiv(*shader, GL_COMPILE_STATUS, &status);
    if (status == 0) {
        glDeleteShader(*shader);
        return NO;
    }
    
    return YES;
}

//------------------------------------------------------

- (BOOL)linkProgram:(GLuint)prog
{
    GLint status;
    glLinkProgram(prog);
    
#if defined(DEBUG)
    GLint logLength;
    glGetProgramiv(prog, GL_INFO_LOG_LENGTH, &logLength);
    if (logLength > 0) {
        GLchar *log = (GLchar *)malloc(logLength);
        glGetProgramInfoLog(prog, logLength, &logLength, log);
        NSLog(@"Program link log:\n%s", log);
        free(log);
    }
#endif
    
    glGetProgramiv(prog, GL_LINK_STATUS, &status);
    if (status == 0) {
        return NO;
    }
    
    return YES;
}

//------------------------------------------------------

- (BOOL)validateProgram:(GLuint)prog
{
    GLint logLength, status;
    
    glValidateProgram(prog);
    glGetProgramiv(prog, GL_INFO_LOG_LENGTH, &logLength);
    if (logLength > 0) {
        GLchar *log = (GLchar *)malloc(logLength);
        glGetProgramInfoLog(prog, logLength, &logLength, log);
        NSLog(@"Program validate log:\n%s", log);
        free(log);
    }
    
    glGetProgramiv(prog, GL_VALIDATE_STATUS, &status);
    if (status == 0) {
        return NO;
    }
    
    return YES;
}


//UTil Method
//------------------------------------------------------

+ (CVPixelBufferRef)pixelBufferFromImage:(CGImageRef)image {
    CGSize frameSize = CGSizeMake(CGImageGetWidth(image), CGImageGetHeight(image)); // Not sure why this is even necessary, using CGImageGetWidth/Height in status/context seems to work fine too

    CVPixelBufferRef pixelBuffer = NULL;
    CVReturn status = CVPixelBufferCreate(kCFAllocatorDefault, frameSize.width, frameSize.height, kCVPixelFormatType_32BGRA, nil, &pixelBuffer);
    if (status != kCVReturnSuccess) {
        return NULL;
    }

    CVPixelBufferLockBaseAddress(pixelBuffer, 0);
    void *data = CVPixelBufferGetBaseAddress(pixelBuffer);
    CGColorSpaceRef rgbColorSpace = CGColorSpaceCreateDeviceRGB();
    CGContextRef context = CGBitmapContextCreate(data, frameSize.width, frameSize.height, 8, CVPixelBufferGetBytesPerRow(pixelBuffer), rgbColorSpace, (CGBitmapInfo) kCGBitmapByteOrder32Little | kCGImageAlphaPremultipliedFirst);
    CGContextDrawImage(context, CGRectMake(0, 0, CGImageGetWidth(image), CGImageGetHeight(image)), image);

    CGColorSpaceRelease(rgbColorSpace);
    CGContextRelease(context);
    CVPixelBufferUnlockBaseAddress(pixelBuffer, 0);

    return pixelBuffer;
}


@end

