@echo off
call Scripts\tracJobEnv.cmd

python -E %PY_HOME%\Scripts\tracd-script.py -p 7090 -b 127.0.0.1 --protocol=ajp --base-path=/FDMtrac -e %TRAC_PROJ_DIR% >> %LOG_DIR%\server.log 2>&1
