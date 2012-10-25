@echo on
setlocal
call %~dp0..\Scripts\tracJobEnv.cmd
cd /d %~dp0

if not exist %PROC_ROOT% mkdir %PROC_ROOT%
if not exist %SVN_PROC_DIR% mkdir %SVN_PROC_DIR%
if not exist %TRAC_SVN_CS_DIR% mkdir %TRAC_SVN_CS_DIR%


:loop
python  dumpSVNTracInfo.py  > %SVN_PROC_DIR%\svnTracInfo.tmp
move /Y %SVN_PROC_DIR%\svnTracInfo.tmp %TRAC_SVN_INFO%


REM Process changesets

for %%f in (%TRAC_SVN_CS_DIR%\*.cmd) do (
 call %%f
 del %%f
)

timeout /t 300  /nobreak > nul
goto :loop 
endlocal