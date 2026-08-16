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

# Usa uma release estável do python-for-android (Python 3.11.5),
# em vez do master (que usa Python 3.14 e quebra o Kivy 2.3.0).
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 0
