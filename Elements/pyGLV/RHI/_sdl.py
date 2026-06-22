from __future__ import annotations

import importlib.abc
import importlib.machinery
import os
import re
import sys
from pathlib import Path


os.environ.setdefault("SDL_CHECK_VERSION", "0")
os.environ.setdefault("SDL_DOC_GENERATOR", "0")


_ASSERT_LEVEL_REPLACEMENT = """if SDL_ASSERT_LEVEL == 0:
    SDL_assert: abc.Callable[[bool], None] = lambda condition: SDL_disabled_assert(condition)
    SDL_assert_release: abc.Callable[[bool], None] = lambda condition: SDL_disabled_assert(condition)
    SDL_assert_paranoid: abc.Callable[[bool], None] = lambda condition: SDL_disabled_assert(condition)
elif SDL_ASSERT_LEVEL == 1:
    SDL_assert: abc.Callable[[bool], None] = lambda condition: SDL_disabled_assert(condition)
    SDL_assert_release: abc.Callable[[bool], None] = lambda condition: SDL_enabled_assert(condition)
    SDL_assert_paranoid: abc.Callable[[bool], None] = lambda condition: SDL_disabled_assert(condition)
elif SDL_ASSERT_LEVEL == 2:
    SDL_assert: abc.Callable[[bool], None] = lambda condition: SDL_enabled_assert(condition)
    SDL_assert_release: abc.Callable[[bool], None] = lambda condition: SDL_enabled_assert(condition)
    SDL_assert_paranoid: abc.Callable[[bool], None] = lambda condition: SDL_disabled_assert(condition)
elif SDL_ASSERT_LEVEL == 3:
    SDL_assert: abc.Callable[[bool], None] = lambda condition: SDL_enabled_assert(condition)
    SDL_assert_release: abc.Callable[[bool], None] = lambda condition: SDL_enabled_assert(condition)
    SDL_assert_paranoid: abc.Callable[[bool], None] = lambda condition: SDL_enabled_assert(condition)
else:
    SDL_enabled_assert(False)
"""


class _PySDL3CompatibilityLoader(importlib.abc.SourceLoader):
    def __init__(self, path: Path) -> None:
        self._path = path

    def get_filename(self, fullname: str) -> str:
        return str(self._path)

    def get_data(self, path: str) -> bytes:
        return Path(path).read_bytes()

    def source_to_code(self, data, path: str, *, _optimize: int = -1):
        source = data.decode("utf-8")
        source = _transform_pysdl3_source(source, Path(path))
        return compile(source, path, "exec", dont_inherit=True, optimize=_optimize)


class _PySDL3CompatibilityFinder(importlib.abc.MetaPathFinder):
    def __init__(self, package_path: Path) -> None:
        self._package_path = package_path

    def find_spec(self, fullname: str, path=None, target=None):
        if fullname == "sdl3":
            return self._module_spec(fullname, self._package_path / "__init__.py", True)

        if not fullname.startswith("sdl3."):
            return None

        relative_path = self._package_path.joinpath(*fullname.split(".")[1:])
        init_path = relative_path / "__init__.py"
        if init_path.exists():
            return self._module_spec(fullname, init_path, True)

        module_path = relative_path.with_suffix(".py")
        if module_path.exists():
            return self._module_spec(fullname, module_path, False)

        return None

    def _module_spec(self, fullname: str, path: Path, is_package: bool):
        spec = importlib.machinery.ModuleSpec(
            fullname,
            _PySDL3CompatibilityLoader(path),
            origin=str(path),
            is_package=is_package,
        )
        spec.has_location = True
        if is_package:
            spec.submodule_search_locations = [str(path.parent)]
        return spec


def _install_py39_pysdl3_hook() -> None:
    if any(isinstance(finder, _PySDL3CompatibilityFinder) for finder in sys.meta_path):
        return

    spec = importlib.machinery.PathFinder.find_spec("sdl3")
    if spec is None or not spec.submodule_search_locations:
        return

    sys.meta_path.insert(0, _PySDL3CompatibilityFinder(Path(spec.submodule_search_locations[0])))


def _transform_pysdl3_source(source: str, path: Path) -> str:
    source = source.replace(
        "descriptions[__index := __index + 1]",
        "descriptions[(__index := __index + 1)]",
    )

    if path.name == "SDL_assert.py":
        source = re.sub(
            r"^match SDL_ASSERT_LEVEL:\n.*?(?=^SDL_assert_always:)",
            _ASSERT_LEVEL_REPLACEMENT,
            source,
            flags=re.MULTILINE | re.DOTALL,
        )

    return _add_future_annotations(source)


def _add_future_annotations(source: str) -> str:
    if "from __future__ import annotations" in source:
        return source

    if source.startswith("\ufeff"):
        source = source[1:]

    if source.startswith('"""') or source.startswith("'''"):
        quote = source[:3]
        end = source.find(quote, 3)
        if end != -1:
            end += 3
            return source[:end] + "\n\nfrom __future__ import annotations\n" + source[end:]

    return "from __future__ import annotations\n" + source


if sys.version_info < (3, 10):
    _install_py39_pysdl3_hook()

try:
    import sdl3 as sdl
except ModuleNotFoundError as exc:
    raise RuntimeError("Elements.pyGLV.RHI requires PySDL3 to be installed.") from exc
except SyntaxError as exc:
    raise RuntimeError(
        "PySDL3 could not be imported on this Python version. "
        "Elements.pyGLV.RHI installs a Python 3.9 compatibility loader for PySDL3, "
        "but the installed PySDL3 package contains unsupported syntax that the loader "
        "does not know how to translate yet."
    ) from exc


__all__ = ["sdl"]
