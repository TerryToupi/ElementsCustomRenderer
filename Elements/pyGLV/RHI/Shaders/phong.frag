#version 450

layout(location = 0) in vec4 inPosition;
layout(location = 1) in vec4 inColor;
layout(location = 2) in vec3 inNormal;

layout(std140, set = 3, binding = 0) uniform LightingBlock
{
    vec4 ambientColor;
    vec4 viewPosition;
    vec4 lightPosition;
    vec4 lightColor;
    vec4 materialColor;
    vec4 scalars;
} lighting;

layout(location = 0) out vec4 outColor;

void main()
{
    vec3 norm = normalize(inNormal);
    vec3 lightDir = normalize(lighting.lightPosition.xyz - inPosition.xyz);
    vec3 viewDir = normalize(lighting.viewPosition.xyz - inPosition.xyz);
    vec3 reflectDir = reflect(-lightDir, norm);

    float ambientStrength = lighting.scalars.x;
    float lightIntensity = lighting.scalars.y;
    float shininess = lighting.scalars.z;

    vec3 ambient = ambientStrength * lighting.ambientColor.xyz;
    float diffuseStrength = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diffuseStrength * lighting.lightColor.xyz;
    float specularStrength = pow(max(dot(viewDir, reflectDir), 0.0), 32.0);
    vec3 specular = shininess * specularStrength * inColor.xyz;

    vec3 result = (ambient + (diffuse + specular) * lightIntensity) * lighting.materialColor.xyz * inColor.xyz;
    outColor = vec4(result, inColor.a);
}
