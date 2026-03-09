from __future__ import annotations

import base64
import ctypes
import json
import sys
from ctypes import wintypes
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SECURE_STORE_FILE = PROJECT_ROOT / "data" / "runtime_secure_store.json"
APP_ENTROPY = b"rag-game-qa-system::runtime-secret-store"


class SecureStorageError(RuntimeError):
    """Raised when local secure storage is unavailable or fails."""


def secure_storage_supported() -> bool:
    return sys.platform == "win32"


if secure_storage_supported():
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_char)),
        ]

    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(DATA_BLOB),
        wintypes.LPCWSTR,
        ctypes.POINTER(DATA_BLOB),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(DATA_BLOB),
    ]
    crypt32.CryptProtectData.restype = wintypes.BOOL

    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(DATA_BLOB),
        ctypes.POINTER(wintypes.LPWSTR),
        ctypes.POINTER(DATA_BLOB),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(DATA_BLOB),
    ]
    crypt32.CryptUnprotectData.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [wintypes.HLOCAL]
    kernel32.LocalFree.restype = wintypes.HLOCAL


def _build_blob(raw: bytes) -> tuple[DATA_BLOB, ctypes.Array[ctypes.c_char]]:
    buffer = ctypes.create_string_buffer(raw)
    blob = DATA_BLOB(len(raw), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    return blob, buffer


def _protect_bytes(raw: bytes) -> bytes:
    if not secure_storage_supported():
        raise SecureStorageError("secure_local mode is only available on Windows hosts")

    data_blob, data_buffer = _build_blob(raw)
    entropy_blob, entropy_buffer = _build_blob(APP_ENTROPY)
    result_blob = DATA_BLOB()
    ctypes.cast(data_buffer, ctypes.c_void_p)
    ctypes.cast(entropy_buffer, ctypes.c_void_p)

    if not crypt32.CryptProtectData(
        ctypes.byref(data_blob),
        "RAG Game QA Runtime Secret",
        ctypes.byref(entropy_blob),
        None,
        None,
        0x01,
        ctypes.byref(result_blob),
    ):
        raise ctypes.WinError()

    try:
        return ctypes.string_at(result_blob.pbData, result_blob.cbData)
    finally:
        kernel32.LocalFree(result_blob.pbData)


def _unprotect_bytes(raw: bytes) -> bytes:
    if not secure_storage_supported():
        raise SecureStorageError("secure_local mode is only available on Windows hosts")

    data_blob, data_buffer = _build_blob(raw)
    entropy_blob, entropy_buffer = _build_blob(APP_ENTROPY)
    result_blob = DATA_BLOB()
    description = wintypes.LPWSTR()
    ctypes.cast(data_buffer, ctypes.c_void_p)
    ctypes.cast(entropy_buffer, ctypes.c_void_p)

    if not crypt32.CryptUnprotectData(
        ctypes.byref(data_blob),
        ctypes.byref(description),
        ctypes.byref(entropy_blob),
        None,
        None,
        0x01,
        ctypes.byref(result_blob),
    ):
        raise ctypes.WinError()

    try:
        return ctypes.string_at(result_blob.pbData, result_blob.cbData)
    finally:
        if description:
            kernel32.LocalFree(description)
        kernel32.LocalFree(result_blob.pbData)


def save_secure_payload(payload: Dict[str, Any]) -> None:
    encrypted = _protect_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    SECURE_STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    envelope = {
        "version": 1,
        "storage": "windows-dpapi",
        "payload": base64.b64encode(encrypted).decode("ascii"),
    }
    SECURE_STORE_FILE.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")


def load_secure_payload() -> Dict[str, Any]:
    if not SECURE_STORE_FILE.exists():
        return {}

    try:
        envelope = json.loads(SECURE_STORE_FILE.read_text(encoding="utf-8"))
        encrypted = base64.b64decode(envelope.get("payload", ""))
        if not encrypted:
            return {}
        decrypted = _unprotect_bytes(encrypted)
        return json.loads(decrypted.decode("utf-8"))
    except Exception as exc:
        raise SecureStorageError(f"failed to load secure payload: {exc}") from exc


def clear_secure_payload() -> None:
    if SECURE_STORE_FILE.exists():
        SECURE_STORE_FILE.unlink()
