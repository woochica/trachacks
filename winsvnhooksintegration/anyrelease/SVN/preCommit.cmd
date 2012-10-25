@echo off
REM arg 1 trac project name. arg 2,3... are same as pre-commit args provided by subversion


REM strip quotes 
SET PName=%1
SET PRepo=%2
SET PTxn=%3
set PName=%PName:"=%
set PRepo=%PRepo:"=%
set PTxn=-t %PTxn:"=%

setlocal 

call %~dp0..\Scripts\tracJobEnv.cmd

REM First Get commit message

for /f "tokens=1,2* delims= " %%i in ('svnlook log %PRepo% %PTxn%   ^| findstr /r /c:"\<Refs \#[0-9][0-9]* "') do (
    set T1=%%j
	set T2=%%k
)

set #=%T2%
set length=0
:loopLen
if defined # (set #=%#:~1%&set /A length += 1&goto loopLen)

rem echo length of "%T2%" is %length%
rem @echo on
if %length% LSS 15 (
  set ERRMSG=DID NOT MEET COMMENT LENGTH REQUIREMENTS
  goto errorMsg
)
echo "%T2%" | findstr /r "#[0-9] ticket:[0-9]" 
if %errorlevel% equ 0 (
  set ERRMSG=COMMENT CONTAINS # or :
  goto errorMsg
)
REM Now we check user against authorized as well as ticket #
for /f  "tokens=1,2* delims= " %%i in ('svnlook author %PRepo% %PTxn%') do (
        set TA=%%i
)

Rem is author ticket owner
findstr /b  /c:"T|%PName%|%T1%|%TA%|" %TRAC_SVN_INFO%
if %errorlevel% equ 0 goto successEnd
Rem does ticket exist
findstr /b  /c:"T|%PName%|%T1%|" %TRAC_SVN_INFO%
if %errorlevel% gtr 0 (
	set ERRMSG=TICKET %T1% DOES NOT EXIST OR IS CLOSED
	goto errorMsg
)
Rem Does author belong to group having access to override
findstr /b /l /c:"G|%PName%|%SVN_PRIV_TRAC_GRP%|%TA%|" %TRAC_SVN_INFO%
if %errorlevel% equ 0 goto successEnd


set ERRMSG=YOU DO NOT HAVE ACCESS TO UPDATE TICKET ASSIGNED TO SOMEONE ELSE 

:errorMsg  
 echo. 1>&2  
 echo Your commit has been blocked - %ERRMSG%. 1>&2  
 echo Commit Message must be as follows 1>&2
 echo   Refs #^<tickNum^> ^<msg^> 1>&2
 echo where 1>&2
 echo   ^<tickNum^> is the ticket number assigned to you (not QC SCR#) 1>&2
 echo   ^<msg^> must be a minimum of 15 characters and must NOT contain a #? or :? 1>&2
 echo. 1>&2
endlocal
exit /B 1

:successEnd
endlocal
exit /B 0