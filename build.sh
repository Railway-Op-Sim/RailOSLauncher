SITE_PACKAGES=$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
pyinstaller -F --noconsole --paths=$SITE_PACKAGES --icon='img/RailOSLauncher.ico' --clean railos_launcher.py
