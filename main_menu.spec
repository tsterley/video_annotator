# -*- mode: python -*-
from kivy.deps import sdl2, glew

block_cipher = None


a = Analysis(['main_menu.py'],
             pathex=['C:\\Users\\User\\Documents\\video-annot'],
             binaries=[],
             datas=[('C:\\Python27\\opencv_ffmpeg331_64.dll', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

# a.datas += [('menu.kv', 'menu.kv', 'DATA')]

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
          name='main_menu',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
