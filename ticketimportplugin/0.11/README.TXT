
This module makes it possible to import tickets in batch, from a Microsoft Excel spreadsheet or a CSV file. User documentation is provided directly in the "Import" tab, that appears in the Trac UI when the module is installed and when the user has IMPORT_EXECUTE permission.

Support for CSV comes out-of-the-box. To be able to import Excel files, xlrd must be installed. xlrd is a Python library, not a Trac plugin. Take the latest binary from http://pypi.python.org/pypi/xlrd. On windows, run the installer; on other platforms, just unzip the .zip, and copy the "xlrd" folder that it contains, into the "site-packages" folder of the Python lib folder, running typically:

mkdir tmp
cd tmp
curl http://pypi.python.org/packages/source/x/xlrd/xlrd-0.6.1.zip > xlrd-0.6.1.zip
unzip xlrd-0.6.1.zip
sudo cp -r xlrd-0.6.1/xlrd /usr/lib/python2.4/site-packages/

No configuration is needed. To verify that it's correctly installed, run "python -c 'import xlrd'" from the command line: it should not cause an error.


A few optional settings can be defined in trac.ini, under the section '[importer]':
- reconciliate_by_owner_also: whether to reconciliate by owner and summary, or by summary only
- skip_lines_with_empty_owner: whether to skip the lines that have an empty value for the owner column, if present.

