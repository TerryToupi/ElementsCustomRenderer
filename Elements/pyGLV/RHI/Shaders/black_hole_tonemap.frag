#version 450

layout(location = 0) in vec2 inUV;
layout(location = 0) out vec4 outColor;

layout(set = 2, binding = 0) uniform sampler2D hdrImage;

vec3 filmicTonemap(vec3 color)
{
    color = max(color, vec3(0.0));
    color = color * (2.51 * color + 0.03) / (color * (2.43 * color + 0.59) + 0.14);
    return pow(clamp(color, 0.0, 1.0), vec3(1.0 / 2.2));
}

void main()
{
    vec3 hdr = texture(hdrImage, inUV).rgb;
    vec2 texel = 1.0 / vec2(textureSize(hdrImage, 0));
    vec3 bloom = vec3(0.0);

    bloom += texture(hdrImage, inUV + texel * vec2(2.0, 0.0)).rgb;
    bloom += texture(hdrImage, inUV + texel * vec2(-2.0, 0.0)).rgb;
    bloom += texture(hdrImage, inUV + texel * vec2(0.0, 2.0)).rgb;
    bloom += texture(hdrImage, inUV + texel * vec2(0.0, -2.0)).rgb;
    bloom *= 0.035;

    outColor = vec4(filmicTonemap(hdr + bloom), 1.0);
}
