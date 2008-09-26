echo 'BUILDING EGG'
python setup.py --verbose bdist_egg
echo ''
echo 'Deploying EGG'
c:\Python25\Scripts\easy_install.exe --verbose --always-unzip dist\testManagementPlugin-0.11.3-py2.5.egg
