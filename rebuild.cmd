@echo off

echo remove files
rmdir/S/Q dist
rmdir/S/Q build
rmdir/S/Q __pycache__

echo write build date
python -c "from datetime import datetime; open('build_date.txt','w').write(datetime.now().strftime('%%Y/%%m/%%d'))"

echo build python
python -m PyInstaller mpw2.spec

echo remove build files
rmdir/S/Q build
rmdir/S/Q __pycache__

@REM echo copy test_program
@REM rmdir/S/Q beta_program
@REM xcopy .\dist .\beta_program /e /h /k /I

powershell -command "Compress-Archive -Path .\dist\* -DestinationPath mpw2.zip"

echo python module list up
make_module_list.cmd