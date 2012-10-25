@echo off
setlocal 
REM strip quotes 
SET PName=%1
SET PRepo=%2
SET PTxn=%3
set PName=%PName:"=%
set PRepo=%PRepo:"=%
set PTxn=%PTxn:"=%

call %~dp0..\Scripts\tracJobEnv.cmd

set filePrefix=%PName%%date:~-4%%date:~4,2%%date:~7,2%%time:~0,2%%time:~3,2%%time:~6,2%-%random%
set filePrefix=%filePrefix: =0%

echo trac-admin %TRAC_PROJ_DIR%\%PName% changeset modified "%PRepo%" "%PTxn%" > %TRAC_SVN_CS_DIR%\%filePrefix%.tmp
move %TRAC_SVN_CS_DIR%\%filePrefix%.tmp %TRAC_SVN_CS_DIR%\%filePrefix%.cmd
exit /B 0
endlocal