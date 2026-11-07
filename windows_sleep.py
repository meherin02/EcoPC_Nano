"""Send an explicitly requested sleep command to Windows."""

import ctypes
import sys
from ctypes import wintypes


class Luid(ctypes.Structure):
    _fields_ = [('low', wintypes.DWORD), ('high', wintypes.LONG)]


class TokenPrivileges(ctypes.Structure):
    _fields_ = [('count', wintypes.DWORD), ('luid', Luid), ('attributes', wintypes.DWORD)]


def sleep_windows():
    if sys.platform != 'win32':
        raise OSError('Windows sleep is available only on the local Windows PC.')

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    security = ctypes.WinDLL('advapi32', use_last_error=True)
    power = ctypes.WinDLL('powrprof', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    security.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    security.LookupPrivilegeValueW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.POINTER(Luid)]
    security.AdjustTokenPrivileges.argtypes = [
        wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(TokenPrivileges),
        wintypes.DWORD, ctypes.POINTER(TokenPrivileges), ctypes.POINTER(wintypes.DWORD),
    ]
    power.SetSuspendState.argtypes = [ctypes.c_ubyte] * 3
    power.SetSuspendState.restype = ctypes.c_ubyte

    token = wintypes.HANDLE()
    if not security.OpenProcessToken(kernel.GetCurrentProcess(), 0x20 | 0x08, ctypes.byref(token)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        privilege = TokenPrivileges(count=1, attributes=2)
        if not security.LookupPrivilegeValueW(None, 'SeShutdownPrivilege', ctypes.byref(privilege.luid)):
            raise ctypes.WinError(ctypes.get_last_error())
        previous = TokenPrivileges()
        returned = wintypes.DWORD()
        ctypes.set_last_error(0)
        adjusted = security.AdjustTokenPrivileges(token, False, ctypes.byref(privilege),
            ctypes.sizeof(previous), ctypes.byref(previous), ctypes.byref(returned))
        error = ctypes.get_last_error()
        if not adjusted or error:
            raise ctypes.WinError(error)
        try:
            if not power.SetSuspendState(False, False, False):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            security.AdjustTokenPrivileges(token, False, ctypes.byref(previous), 0, None, None)
    finally:
        kernel.CloseHandle(token)
