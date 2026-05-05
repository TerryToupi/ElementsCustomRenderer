#version 450

layout(location = 0) in vec2 in_uv;
layout(location = 0) out vec4 out_color;

void main()
{
    out_color = vec4(1.0, 0.28 + in_uv.y * 0.35, 0.12 + in_uv.x * 0.45, 1.0);
}
