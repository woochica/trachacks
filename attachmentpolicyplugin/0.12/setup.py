from setuptools import find_packages, setup

# name can be any name.  This name will be used to create the .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='Attachment Policy Plugin', 
    version='0.1.0',
    author = 'Gefasoft AG, Franz Mayer',
    author_email = 'franz.mayer@gefasoft.de', 
    description = 'Adds permission TICKET_ATTACHMENT_DELETE, so deleting attachments can be done without giving permission TICKET_ADMIN',
    url = 'http://www.gefasoft-muenchen.de',
#    download_url = 'https://trac-hacks.org/wiki/BudgetingPlugin',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        attachmentpolicy = attachmentpolicy
    """
)

