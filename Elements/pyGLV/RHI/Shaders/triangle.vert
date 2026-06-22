#version 450

layout(location = 0) out vec2 out_uv;

vec2 positions[3] = vec2[](
    vec2(0.0, -0.8),
    vec2(0.8, 0.8),
    vec2(-0.8, 0.8)
);

void main()
{
    vec2 position = positions[gl_VertexIndex];
    gl_Position = vec4(position, 0.0, 1.0);
    out_uv = position * 0.5 + vec2(0.5);
}
