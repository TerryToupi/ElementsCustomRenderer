#version 450

layout(location = 0) in vec4 inPosition;
layout(location = 1) in vec4 inColor;
layout(location = 2) in vec3 inNormal;

layout(std140, set = 3, binding = 0) uniform PBRBlock
{
    vec4 viewPosition;
    vec4 lightPosition;
    vec4 lightColor;
    vec4 albedoColor;
    vec4 materialParams;
    vec4 ambientParams;
} pbr;

layout(location = 0) out vec4 outColor;

const float PI = 3.14159265359;

float distributionGGX(vec3 normal, vec3 halfway, float roughness)
{
    float a = roughness * roughness;
    float a2 = a * a;
    float nDotH = max(dot(normal, halfway), 0.0);
    float nDotH2 = nDotH * nDotH;

    float denom = (nDotH2 * (a2 - 1.0) + 1.0);
    denom = PI * denom * denom;

    return a2 / max(denom, 0.0001);
}

float geometrySchlickGGX(float nDotV, float roughness)
{
    float r = roughness + 1.0;
    float k = (r * r) / 8.0;
    return nDotV / max(nDotV * (1.0 - k) + k, 0.0001);
}

float geometrySmith(vec3 normal, vec3 viewDir, vec3 lightDir, float roughness)
{
    float nDotV = max(dot(normal, viewDir), 0.0);
    float nDotL = max(dot(normal, lightDir), 0.0);
    return geometrySchlickGGX(nDotV, roughness) *
           geometrySchlickGGX(nDotL, roughness);
}

vec3 fresnelSchlick(float cosTheta, vec3 f0)
{
    return f0 + (1.0 - f0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

void main()
{
    float metallic = clamp(pbr.materialParams.x, 0.0, 1.0);
    float roughness = clamp(pbr.materialParams.y, 0.04, 1.0);
    float ao = clamp(pbr.materialParams.z, 0.0, 1.0);
    float lightIntensity = max(pbr.materialParams.w, 0.0);
    float ambientStrength = max(pbr.ambientParams.x, 0.0);

    vec3 albedo = pow(clamp(pbr.albedoColor.rgb * inColor.rgb, 0.0, 1.0), vec3(2.2));
    vec3 normal = normalize(inNormal);
    vec3 viewDir = normalize(pbr.viewPosition.xyz - inPosition.xyz);
    vec3 lightDir = normalize(pbr.lightPosition.xyz - inPosition.xyz);
    vec3 halfway = normalize(viewDir + lightDir);

    vec3 f0 = mix(vec3(0.04), albedo, metallic);
    float ndf = distributionGGX(normal, halfway, roughness);
    float geometry = geometrySmith(normal, viewDir, lightDir, roughness);
    vec3 fresnel = fresnelSchlick(max(dot(halfway, viewDir), 0.0), f0);

    vec3 numerator = ndf * geometry * fresnel;
    float denominator = 4.0 * max(dot(normal, viewDir), 0.0) *
                        max(dot(normal, lightDir), 0.0) + 0.0001;
    vec3 specular = numerator / denominator;

    vec3 kS = fresnel;
    vec3 kD = (vec3(1.0) - kS) * (1.0 - metallic);

    float distanceToLight = length(pbr.lightPosition.xyz - inPosition.xyz);
    float attenuation = 1.0 / max(distanceToLight * distanceToLight, 0.01);
    vec3 radiance = pbr.lightColor.rgb * lightIntensity * attenuation;
    float nDotL = max(dot(normal, lightDir), 0.0);

    vec3 direct = (kD * albedo / PI + specular) * radiance * nDotL;
    vec3 ambient = ambientStrength * albedo * ao;
    vec3 color = ambient + direct;

    color = color / (color + vec3(1.0));
    color = pow(color, vec3(1.0 / 2.2));

    outColor = vec4(color, inColor.a);
}
