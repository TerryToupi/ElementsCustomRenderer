#version 450

layout(location = 0) in vec4 vPosition;
layout(location = 1) in vec4 vColor;
layout(location = 2) in vec4 vNormal;

layout(std140, set = 1, binding = 0) uniform TransformBlock
{
    mat4 modelViewProj;
    mat4 model;
} transform;

layout(location = 0) out vec4 outPosition;
layout(location = 1) out vec4 outColor;
layout(location = 2) out vec3 outNormal;

void main()
{
    gl_Position = transform.modelViewProj * vPosition;
    outPosition = transform.model * vPosition;
    outColor = vColor;
    outNormal = mat3(transpose(inverse(transform.model))) * vNormal.xyz;
}
