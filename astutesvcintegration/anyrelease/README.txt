READ ENTIRE DOCUMENT BEFORE STARTING

To install the service named Test run the following command

           AstuteSvc -i Test

 The service created will be named AstuteSvcTest
 The file AstuteSvcTest.ini must exists in the same directory as AstuteSvc.exe. See the provided AstuteSvcSample.ini file on the options.
 

To un-install the service named Test run the following command

           AstuteSvc -u Test



When the service runs it creates the process as specified in the ini file. 
It checks the process is active every 5 seconds and restarts the process if it is not active

Notes: 
. You need privilige to create a service. In newer windows systems it may not be enough if you log in as administrator. Right click on the command prompt and select 'Run as Administrator'.