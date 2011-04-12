from setuptools import find_packages, setup
setup(
    name='MultipleWorkflowPlugin',
    version='1.0',
    license = "New BSD",
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        MultipleWorkflowPlugin =MultipleWorkflowPlugin
    """,
)

