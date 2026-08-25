"""Bible Commentary Translator.

Shared library behind the notebooks. Every notebook imports from here rather
than carrying its own copy of the code -- the two scrapers were previously
duplicated byte-for-byte across two notebooks, which is what this package
exists to prevent.
"""

__version__ = "0.1.0"
