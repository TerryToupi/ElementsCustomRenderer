#version 450

struct Particle
{
    vec4 position;
    vec4 velocity;
};

layout(set = 0, binding = 0) readonly buffer Particles
{
    Particle particles[];
};

layout(location = 0) out vec4 outColor;

void main()
{
    Particle particle = particles[gl_VertexIndex];
    vec2 position = particle.position.xy;
    vec2 velocity = particle.velocity.xy;

    float speed = clamp(length(velocity) * 1.7, 0.0, 1.0);
    vec3 slowColor = vec3(0.18, 0.55, 1.0);
    vec3 fastColor = vec3(1.0, 0.38, 0.12);

    gl_Position = vec4(position, 0.0, 1.0);
    gl_PointSize = 3.0 + speed * 3.0;
    outColor = vec4(mix(slowColor, fastColor, speed), 0.92);
}
