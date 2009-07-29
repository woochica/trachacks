from trac.core import Interface

class IRequireComponents(Interface):
    def requires():
        """list of component classes that this component depends on"""
