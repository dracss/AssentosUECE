[app]
title = Assentos UECE
package.name = assentosuece
package.domain = br.uece
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf
source.exclude_dirs = AssentosUECE, bin, tests, __pycache__
version = 0.1
requirements = python3,kivy==2.3.0,kivymd==1.1.1,pillow,fpdf2,defusedxml,fonttools
orientation = portrait
fullscreen = 0

# Android build configuration
android.api = 34
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

[buildozer]
log_level = 2
warn_on_root = 0
