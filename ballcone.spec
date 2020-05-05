# -*- mode: python ; coding: utf-8 -*-

import geolite2
import monetdblite

geolite2_city = geolite2.geolite2_database()
libmonetdb5 = monetdblite.embeddedmonetdb.dll._name

block_cipher = None

a = Analysis(['ballcone/__main__.py'],
             binaries=[(libmonetdb5, 'monetdblite')],
             datas=[(geolite2_city, '_maxminddb_geolite2')],
             hiddenimports=[],
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
