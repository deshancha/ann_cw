varying highp vec2 texCoords;
precision highp float;

uniform sampler2D SamplerY;
uniform sampler2D SamplerUV;
uniform sampler2D SamplerTextureMask;
uniform mat3 colorConversionMatrix;
uniform highp float shiftVal;
uniform highp float angleInDegrees;
uniform highp float luminanceThreshold;
uniform highp float enableMask;
uniform highp float maskPivotX;
uniform highp float maskPivotY;
uniform highp float startingXOffset;
uniform int background; // 1 black, 2 white, 3 blur

// =============================================================================================

vec3 getFragColor(vec3 textureColor, vec3 textureColor2, float columnWidth)
{
   return textureColor;
}

bool checkLuminanceThresholdLessThanOne(vec3 rgb)
{
    highp float luminance = dot(rgb, vec3(0.2125, 0.7154, 0.0721));
    highp float thresholdResult = step(luminanceThreshold, luminance);
    
    return thresholdResult < 1.0;
}

vec2 getTotatedTextureCoordAround(vec2 texCoord, float angleInDegress, float pX, float pY) {
    highp vec2 maskPivot = vec2(pX, pY);
    highp vec2 maskCenteredPoint = texCoord.xy - maskPivot;
    
    float sinFactorMask = sin(radians(angleInDegress));
    float cosFactorMask = cos(radians(angleInDegress));
      
    mat2 rotMatrix = mat2(cosFactorMask, sinFactorMask, -sinFactorMask, cosFactorMask);
    
    vec2 retTextureCoord = maskCenteredPoint  * rotMatrix;
    
    retTextureCoord = retTextureCoord + maskPivot;
    
    return retTextureCoord;
}

float guissianValue(float x, float sigma){
    if (sigma <= 0.0)
        return 0.0;
    return exp(-(x*x)/(2.0 * sigma)) / (2.0 * 3.14157 * sigma);
}


void main()
{
    lowp vec3 yuv;
    lowp vec3 yuv2;
    lowp vec2 texCoords2;
    
    texCoords2.x = texCoords.x + 0.0005 * shiftVal;
    texCoords2.y = texCoords.y;
    
    // start -> rotation of texture coordinate
    
    texCoords2 = getTotatedTextureCoordAround(texCoords2, angleInDegrees, maskPivotX, maskPivotY);
    
    // end -> rotation    
	
	yuv.x = (texture2D(SamplerY, texCoords).r - (16.0/255.0));
	yuv.yz = (texture2D(SamplerUV, texCoords).rg - vec2(0.5, 0.5));
    
    yuv2.x = (texture2D(SamplerY, texCoords2).r - (16.0/255.0));
    yuv2.yz = (texture2D(SamplerUV, texCoords2).rg - vec2(0.5, 0.5));
	
    lowp vec3 textureColor = colorConversionMatrix * yuv;
    lowp vec3 textureColor2 = colorConversionMatrix * yuv2;
    
    // WARNING: should calculate always, don't put inside if statement
    //https://gamedev.stackexchange.com/questions/32543/glsl-if-else-statement-unexpected-behaviour
    lowp vec3 processedFragColor = getFragColor(textureColor, textureColor2, 1.0);
    
    lowp vec3 finalFragColor = processedFragColor;
    
    if (enableMask > 1.0) {
        /* We crop  frame for aspect ratio maintain in gst RGB pipeline before inferencing
         * Without a noticed failure to proper human contour isolation in core ml
         * Frame is 720x720 originally 1280 x 720 and crop left=280, right=280
         * Now left margin: 280/1280 = 0.21875, right: (1280-280)/1280 = 0.78125, span = 0.5625
        */
        float maskU = (texCoords.x - 0.21875) / 0.5625;
        
        // area out of mask we set black
        if (maskU < 0.0 || maskU > 1.0) {
            gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
            return;
        }
        
        float maskVal = 0.0;
        vec2 maskCoord = vec2(maskU, texCoords.y);
        vec2 rotatedMaskTextureCoordinates = getTotatedTextureCoordAround(maskCoord, 180.0, 0.5, 0.5);
        lowp vec4 rgba = texture2D(SamplerTextureMask, rotatedMaskTextureCoordinates);
        
        // Single channel texture (GL_RED_EXT / GL_LUMINANCE mask may be in .r)
        maskVal = rgba.r;
        if (maskVal == 0.0 && rgba.a > 0.0 && rgba.a < 1.0) {
            maskVal = rgba.a;
        }
        
        // Display Mask and return
        if (background == 4) {
            gl_FragColor = vec4(maskVal, maskVal, maskVal, 1.0);
            return;
        }
        
        if (maskVal < 0.5) {
            // Background: Gaussian Blur or replacement color
            vec2 texC = texCoords;
            vec4 texCol = vec4(textureColor, 1.0);
            vec4 gaussCol = vec4(textureColor, 1.0);
            vec2 step = vec2(1.0, 0.0) / vec2(512.0, 512.0);
            for(int i = 1; i <= 32; ++ i)
            {
                float weight = guissianValue( float(i) / 32.0, 1.0 * 0.5 );
                if ( weight < 1.0/255.0 )
                    break;
                
                yuv.x = (texture2D(SamplerY, texC + step * float(i))).r - (16.0/255.0);
                yuv.yz = (texture2D(SamplerUV, texC + step * float(i))).rg - vec2(0.5, 0.5);
                
                texCol = vec4(colorConversionMatrix * yuv, 1.0);
                gaussCol += vec4(texCol.rgb * weight, weight);
                
                yuv.x = (texture2D(SamplerY, texC - step * float(i))).r - (16.0/255.0);
                yuv.yz = (texture2D(SamplerUV, texC - step * float(i))).rg - vec2(0.5, 0.5);
                
                texCol = vec4(colorConversionMatrix * yuv, 1.0);
                gaussCol += vec4(texCol.rgb * weight, weight);
            }
            gaussCol.rgb = clamp(gaussCol.rgb / gaussCol.w, 0.0, 1.0);
            
            if (background == 0 || background == 3) {
                gl_FragColor = vec4(gaussCol.rgb, 1.0); // Gaus blur
            } else if (background == 1) {
                gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0); // White
            } else if (background == 2) {
                gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0); // Black
            } else {
                gl_FragColor = vec4(textureColor, 1.0); // Unblurred
            }
        } else {
            gl_FragColor = vec4(finalFragColor, 1.0);
        }
        
        
    } else {
        gl_FragColor = vec4(finalFragColor, 1.0);
    }
}
