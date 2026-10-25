attribute vec4 position;
attribute vec2 texCoord;


varying vec2 texCoords;

void main()
{
    float cos180 = cos(3.14159);
    float sin180 = sin(3.14159);
    
    mat4 rotationMatrix = mat4( cos180, -sin180, 0.0, 0.0,
                                sin180,  cos180, 0.0, 0.0,
                                  0.0,      0.0, 1.0, 0.0,
                                  0.0,      0.0, 0.0, 1.0);
    
	gl_Position = position  * rotationMatrix;
	texCoords = texCoord;
}

