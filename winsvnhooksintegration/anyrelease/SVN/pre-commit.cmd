call D:\Trac\SVN\preCommit.cmd "TestName" "%1" "%2"
if %errorlevel% gtr 0 exit /B 1
exit /B 0