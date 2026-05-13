from __future__ import annotations

from enum import Enum, IntEnum, IntFlag
from typing import TypeVar


class WindowFlag(IntFlag):
    FULLSCREEN = 1
    OPENGL = 2
    OCCLUDED = 4
    HIDDEN = 8
    BORDERLESS = 16
    RESIZABLE = 32
    MINIMIZED = 64
    MAXIMIZED = 128
    MOUSE_GRABBED = 256
    INPUT_FOCUS = 512
    MOUSE_FOCUS = 1024
    EXTERNAL = 2048
    MODAL = 4096
    HIGH_PIXEL_DENSITY = 8192
    MOUSE_CAPTURE = 16384
    MOUSE_RELATIVE_MODE = 32768
    ALWAYS_ON_TOP = 65536
    UTILITY = 131072
    TOOLTIP = 262144
    POPUP_MENU = 524288
    KEYBOARD_GRABBED = 1048576
    FILL_DOCUMENT = 2097152
    VULKAN = 268435456
    METAL = 536870912
    TRANSPARENT = 1073741824
    NOT_FOCUSABLE = 2147483648


class ShaderFormat(IntFlag):
    INVALID = 0
    PRIVATE = 1
    SPIRV = 2
    DXBC = 4
    DXIL = 8
    MSL = 16
    METALLIB = 32


class ShaderStage(IntEnum):
    VERTEX = 0
    FRAGMENT = 1


class PrimitiveType(IntEnum):
    TRIANGLELIST = 0
    TRIANGLESTRIP = 1
    LINELIST = 2
    LINESTRIP = 3
    POINTLIST = 4


class LoadOp(IntEnum):
    LOAD = 0
    CLEAR = 1
    DONT_CARE = 2


class StoreOp(IntEnum):
    STORE = 0
    DONT_CARE = 1
    RESOLVE = 2
    RESOLVE_AND_STORE = 3


class IndexElementSize(IntEnum):
    BIT16 = 0
    BIT32 = 1


class TextureFormat(IntEnum):
    INVALID = 0
    A8_UNORM = 1
    R8_UNORM = 2
    R8G8_UNORM = 3
    R8G8B8A8_UNORM = 4
    R16_UNORM = 5
    R16G16_UNORM = 6
    R16G16B16A16_UNORM = 7
    R10G10B10A2_UNORM = 8
    B5G6R5_UNORM = 9
    B5G5R5A1_UNORM = 10
    B4G4R4A4_UNORM = 11
    B8G8R8A8_UNORM = 12
    BC1_RGBA_UNORM = 13
    BC2_RGBA_UNORM = 14
    BC3_RGBA_UNORM = 15
    BC4_R_UNORM = 16
    BC5_RG_UNORM = 17
    BC7_RGBA_UNORM = 18
    BC6H_RGB_FLOAT = 19
    BC6H_RGB_UFLOAT = 20
    R8_SNORM = 21
    R8G8_SNORM = 22
    R8G8B8A8_SNORM = 23
    R16_SNORM = 24
    R16G16_SNORM = 25
    R16G16B16A16_SNORM = 26
    R16_FLOAT = 27
    R16G16_FLOAT = 28
    R16G16B16A16_FLOAT = 29
    R32_FLOAT = 30
    R32G32_FLOAT = 31
    R32G32B32A32_FLOAT = 32
    R11G11B10_UFLOAT = 33
    R8_UINT = 34
    R8G8_UINT = 35
    R8G8B8A8_UINT = 36
    R16_UINT = 37
    R16G16_UINT = 38
    R16G16B16A16_UINT = 39
    R32_UINT = 40
    R32G32_UINT = 41
    R32G32B32A32_UINT = 42
    R8_INT = 43
    R8G8_INT = 44
    R8G8B8A8_INT = 45
    R16_INT = 46
    R16G16_INT = 47
    R16G16B16A16_INT = 48
    R32_INT = 49
    R32G32_INT = 50
    R32G32B32A32_INT = 51
    R8G8B8A8_UNORM_SRGB = 52
    B8G8R8A8_UNORM_SRGB = 53
    BC1_RGBA_UNORM_SRGB = 54
    BC2_RGBA_UNORM_SRGB = 55
    BC3_RGBA_UNORM_SRGB = 56
    BC7_RGBA_UNORM_SRGB = 57
    D16_UNORM = 58
    D24_UNORM = 59
    D32_FLOAT = 60
    D24_UNORM_S8_UINT = 61
    D32_FLOAT_S8_UINT = 62
    ASTC_4x4_UNORM = 63
    ASTC_5x4_UNORM = 64
    ASTC_5x5_UNORM = 65
    ASTC_6x5_UNORM = 66
    ASTC_6x6_UNORM = 67
    ASTC_8x5_UNORM = 68
    ASTC_8x6_UNORM = 69
    ASTC_8x8_UNORM = 70
    ASTC_10x5_UNORM = 71
    ASTC_10x6_UNORM = 72
    ASTC_10x8_UNORM = 73
    ASTC_10x10_UNORM = 74
    ASTC_12x10_UNORM = 75
    ASTC_12x12_UNORM = 76
    ASTC_4x4_UNORM_SRGB = 77
    ASTC_5x4_UNORM_SRGB = 78
    ASTC_5x5_UNORM_SRGB = 79
    ASTC_6x5_UNORM_SRGB = 80
    ASTC_6x6_UNORM_SRGB = 81
    ASTC_8x5_UNORM_SRGB = 82
    ASTC_8x6_UNORM_SRGB = 83
    ASTC_8x8_UNORM_SRGB = 84
    ASTC_10x5_UNORM_SRGB = 85
    ASTC_10x6_UNORM_SRGB = 86
    ASTC_10x8_UNORM_SRGB = 87
    ASTC_10x10_UNORM_SRGB = 88
    ASTC_12x10_UNORM_SRGB = 89
    ASTC_12x12_UNORM_SRGB = 90
    ASTC_4x4_FLOAT = 91
    ASTC_5x4_FLOAT = 92
    ASTC_5x5_FLOAT = 93
    ASTC_6x5_FLOAT = 94
    ASTC_6x6_FLOAT = 95
    ASTC_8x5_FLOAT = 96
    ASTC_8x6_FLOAT = 97
    ASTC_8x8_FLOAT = 98
    ASTC_10x5_FLOAT = 99
    ASTC_10x6_FLOAT = 100
    ASTC_10x8_FLOAT = 101
    ASTC_10x10_FLOAT = 102
    ASTC_12x10_FLOAT = 103
    ASTC_12x12_FLOAT = 104


class TextureType(IntEnum):
    TEXTURE_2D = 0
    TEXTURE_2D_ARRAY = 1
    TEXTURE_3D = 2
    CUBE = 3
    CUBE_ARRAY = 4


class TextureUsage(IntFlag):
    SAMPLER = 1
    COLOR_TARGET = 2
    DEPTH_STENCIL_TARGET = 4
    GRAPHICS_STORAGE_READ = 8
    COMPUTE_STORAGE_READ = 16
    COMPUTE_STORAGE_WRITE = 32
    COMPUTE_STORAGE_SIMULTANEOUS_READ_WRITE = 64


class SampleCount(IntEnum):
    SAMPLE_1 = 0
    SAMPLE_2 = 1
    SAMPLE_4 = 2
    SAMPLE_8 = 3


class CubeMapFace(IntEnum):
    POSITIVEX = 0
    NEGATIVEX = 1
    POSITIVEY = 2
    NEGATIVEY = 3
    POSITIVEZ = 4
    NEGATIVEZ = 5


class TransferBufferUsage(IntEnum):
    UPLOAD = 0
    DOWNLOAD = 1


class BufferUsage(IntFlag):
    VERTEX = 1
    INDEX = 2
    INDIRECT = 4
    GRAPHICS_STORAGE_READ = 8
    COMPUTE_STORAGE_READ = 16
    COMPUTE_STORAGE_WRITE = 32


class Filter(IntEnum):
    NEAREST = 0
    LINEAR = 1


class SamplerMipmapMode(IntEnum):
    NEAREST = 0
    LINEAR = 1


class SamplerAddressMode(IntEnum):
    REPEAT = 0
    MIRRORED_REPEAT = 1
    CLAMP_TO_EDGE = 2


class CompareOp(IntEnum):
    INVALID = 0
    NEVER = 1
    LESS = 2
    EQUAL = 3
    LESS_OR_EQUAL = 4
    GREATER = 5
    NOT_EQUAL = 6
    GREATER_OR_EQUAL = 7
    ALWAYS = 8


class StencilOp(IntEnum):
    INVALID = 0
    KEEP = 1
    ZERO = 2
    REPLACE = 3
    INCREMENT_AND_CLAMP = 4
    DECREMENT_AND_CLAMP = 5
    INVERT = 6
    INCREMENT_AND_WRAP = 7
    DECREMENT_AND_WRAP = 8


class FillMode(IntEnum):
    FILL = 0
    LINE = 1


class CullMode(IntEnum):
    NONE = 0
    FRONT = 1
    BACK = 2


class FrontFace(IntEnum):
    COUNTER_CLOCKWISE = 0
    CLOCKWISE = 1


class BlendFactor(IntEnum):
    INVALID = 0
    ZERO = 1
    ONE = 2
    SRC_COLOR = 3
    ONE_MINUS_SRC_COLOR = 4
    DST_COLOR = 5
    ONE_MINUS_DST_COLOR = 6
    SRC_ALPHA = 7
    ONE_MINUS_SRC_ALPHA = 8
    DST_ALPHA = 9
    ONE_MINUS_DST_ALPHA = 10
    CONSTANT_COLOR = 11
    ONE_MINUS_CONSTANT_COLOR = 12
    SRC_ALPHA_SATURATE = 13


class BlendOp(IntEnum):
    INVALID = 0
    ADD = 1
    SUBTRACT = 2
    REVERSE_SUBTRACT = 3
    MIN = 4
    MAX = 5


class ColorComponent(IntFlag):
    R = 1
    G = 2
    B = 4
    A = 8


class VertexElementFormat(IntEnum):
    INVALID = 0
    INT = 1
    INT2 = 2
    INT3 = 3
    INT4 = 4
    UINT = 5
    UINT2 = 6
    UINT3 = 7
    UINT4 = 8
    FLOAT = 9
    FLOAT2 = 10
    FLOAT3 = 11
    FLOAT4 = 12
    BYTE2 = 13
    BYTE4 = 14
    UBYTE2 = 15
    UBYTE4 = 16
    BYTE2_NORM = 17
    BYTE4_NORM = 18
    UBYTE2_NORM = 19
    UBYTE4_NORM = 20
    SHORT2 = 21
    SHORT4 = 22
    USHORT2 = 23
    USHORT4 = 24
    SHORT2_NORM = 25
    SHORT4_NORM = 26
    USHORT2_NORM = 27
    USHORT4_NORM = 28
    HALF2 = 29
    HALF4 = 30


class VertexInputRate(IntEnum):
    VERTEX = 0
    INSTANCE = 1


class PresentMode(IntEnum):
    VSYNC = 0
    IMMEDIATE = 1
    MAILBOX = 2


class SwapchainComposition(IntEnum):
    SDR = 0
    SDR_LINEAR = 1
    HDR_EXTENDED_LINEAR = 2
    HDR10_ST2084 = 3


EnumType = TypeVar("EnumType", bound=Enum)


def to_sdl(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return tuple(to_sdl(item) for item in value)
    if isinstance(value, list):
        return [to_sdl(item) for item in value]
    return value


def from_sdl(enum_type: type[EnumType], value: int) -> EnumType | int:
    try:
        return enum_type(value)
    except ValueError:
        return value
