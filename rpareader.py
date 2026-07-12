import io
import os
from typing import BinaryIO, Dict, Optional

from unrpa import UnRPA
from unrpa.versions.version import Version
from unrpa.view import ArchiveView

import fnmatch


class RPAReader:
    """Read files from RPA archives entirely in memory, without writing to disk."""

    def __init__(self, archive_path: str) -> None:
        self.archive_path = archive_path
        self._archive: Optional[BinaryIO] = None
        self._version: Optional[Version] = None
        self._index: Optional[Dict[str, "tuple"]] = None

    def _ensure_open(self) -> None:
        if self._archive is None:
            self._archive = open(self.archive_path, "rb")
            unrpa = UnRPA(self.archive_path)
            self._version = unrpa.detect_version()
            self._index = unrpa.get_index(self._archive, self._version)

    def close(self) -> None:
        if self._archive is not None:
            self._archive.close()
            self._archive = None

    def __del__(self) -> None:
        self.close()

    @property
    def names(self) -> list:
        self._ensure_open()
        return list(self._index.keys())

    def list_files(self) -> list:
        return sorted(self.names)

    def exists(self, name: str) -> bool:
        self._ensure_open()
        return os.path.normpath(name) in self._index

    def read(self, name: str) -> bytes:
        self._ensure_open()
        name = os.path.normpath(name)
        if name not in self._index:
            raise FileNotFoundError(f"'{name}' not found in archive")
        data = self._index[name]
        offset, length, prefix = next(iter(data))
        view = ArchiveView(self._archive, offset, length, prefix)
        return view.read()

    def open(self, name: str) -> io.BytesIO:
        return io.BytesIO(self.read(name))
    
    # 新增：批量预加载常用资源（大大提升桌宠流畅度）
    def preload(self, patterns: list[str]) -> Dict[str, bytes]:
        """预加载一批文件，例如所有 'sprites/monika/' 下的立绘"""
        self._ensure_open()
        result = {}
        for name in self.names:
            if any(name.startswith(p) or fnmatch.fnmatch(name, p) for p in patterns):
                try:
                    result[name] = self.read(name)
                except:
                    pass
        return result

    # 新增：获取文件流（推荐桌宠使用）
    def open_stream(self, name: str) -> io.BytesIO:
        data = self.read(name)
        return io.BytesIO(data)

    def __len__(self) -> int:
        self._ensure_open()
        return len(self._index)

    def __bool__(self) -> bool:
        return len(self) > 0

    def __contains__(self, name: str) -> bool:
        return self.exists(name)

    def __getitem__(self, name: str) -> bytes:
        return self.read(name)

    def __enter__(self) -> "RPAReader":
        return self

    def __exit__(self, *args) -> None:
        self.close()
