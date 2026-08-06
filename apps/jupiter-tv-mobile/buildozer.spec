[app]
title = Jupiter TV
package.name = jupitertv
package.domain = com.jupiterone
source.dir = .
source.include_exts = py,png,jpg,kv,txt,kt
version = 1.0.0
requirements = python3,kivy==2.3.0,duckdb>=1.0.0

# Fire TV Hardware & Platform Settings
android.archs = arm64-v8a, armeabi-v7a
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b

# Critical Permissions for Live Streaming
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# UI Configuration
orientation = landscape
fullscreen = 1
android.wakelock = True

# Include Native Kotlin Source Directory
android.add_src_dirs = android_native

[buildozer]
log_level = 2
warn_on_root = 1
