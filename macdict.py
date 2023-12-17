from __future__ import absolute_import

import ctypes
import ctypes.util


def find_and_load(name):
    return ctypes.cdll.LoadLibrary(ctypes.util.find_library(name))


objc = find_and_load('objc')
objc.objc_getClass.restype = ctypes.c_void_p
objc.sel_registerName.restype = ctypes.c_void_p
objc.objc_msgSend.restype = ctypes.c_void_p
objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

Foundation = find_and_load('Foundation')
CoreFoundation = find_and_load('CoreFoundation')
CoreServices = find_and_load('CoreServices')

NSString = objc.objc_getClass(b'NSString')
NSAutoreleasePool = objc.objc_getClass(b'NSAutoreleasePool')
Boolean = ctypes.c_uint8
CFIndex = ctypes.c_long
CFStringRef = ctypes.c_void_p
CFStringEncoding = ctypes.c_uint32
CFStringEncodingUTF8 = 0x08000100

CFStringCreateWithBytes = Foundation.CFStringCreateWithBytes
CFStringCreateWithBytes.restype = CFStringRef
CFStringCreateWithBytes.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_char), CFIndex,
    CFStringEncoding, Boolean]


class CFRange(ctypes.Structure):
    _fields_ = [('location', CFIndex), ('length', CFIndex)]


DCSCopyTextDefinition = CoreServices.DCSCopyTextDefinition
DCSCopyTextDefinition.restype = CFStringRef
DCSCopyTextDefinition.argtypes = (ctypes.c_void_p, CFStringRef, CFRange)


def sel_name(name):
    return objc.sel_registerName(name.encode('ascii'))


def lookup_word(word):
    word_bytes = word.encode('utf-8')
    word_cfstring = CFStringCreateWithBytes(
        None, word_bytes, len(word_bytes), CFStringEncodingUTF8, False)
    definition_nsstring = DCSCopyTextDefinition(
        None, word_cfstring, CFRange(0, len(word_bytes)))
    definition = ctypes.c_char_p(objc.objc_msgSend(
        definition_nsstring, sel_name('UTF8String')))
    if definition.value:
        return definition.value.decode('utf-8')


def ensure_unicode(text, encoding):
    if isinstance(text, bytes):
        return text.decode(encoding)
    return text
