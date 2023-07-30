# -*- mode: python ; coding: utf-8 -*-

import geolite2

geolite2_city = geolite2.geolite2_database()

block_cipher = None

a = Analysis(['ballcone/__main__.py'],
             datas=[(geolite2_city, '_maxminddb_geolite2'), ('ballcone/templates', 'templates')],
             hiddenimports=['cmath', 'pkg_resources.py2_warn', 'numpy'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='ballcone',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True)
