#version 450

layout(location = 0) in vec4 vPosition;
layout(location = 1) in vec4 vColor;

layout(std140, set = 1, binding = 0) uniform TransformBlock
{
    mat4 modelViewProj;
} transform;

layout(location = 0) out vec4 outColor;

void main()
{
    gl_Position = transform.modelViewProj * vPosition;
    outColor = vColor;
}
