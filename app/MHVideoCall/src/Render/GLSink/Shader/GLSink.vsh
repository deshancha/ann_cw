attribute vec4 a_position;
attribute vec2 a_texcoord;
varying vec2 v_texcoord;

void main()
{
    float cos180 = cos(3.14159);
    float sin180 = sin(3.14159);
    
    mat4 rotationMatrix = mat4( cos180, -sin180, 0.0, 0.0,
                                sin180,  cos180, 0.0, 0.0,
                                  0.0,      0.0, 1.0, 0.0,
                                  0.0,      0.0, 0.0, 1.0);
    
    gl_Position = a_position ;//* rotationMatrix;
    v_texcoord = a_texcoord;
}
