PyTreex
=======

PyTreex is a minimal implementation of the [Treex](http://ufal.cz/treex) API in Python. 
It has classes and methods for common Treex objects, such as documents, bundles, zones,
trees, nodes, and blocks.

One can run Treex-like scenarios (which are stored in YAML) from the command-line.
However, the current version is not able to read Treex XML files. Treex XML files must be
stored in YAML format using the [Write::YAML](https://github.com/ufal/treex/blob/master/lib/Treex/Block/Write/YAML.pm)
Treex block before using them here.

This Python version of Treex is experimental and its use case is at best marginal; we still
recommend you to use the original, [Perl Treex](https://github.com/ufal/treex).

Installation
------------

PyTreex can be installed directly from GitHub using pip:
```
pip install git+https://github.com/ufal/pytreex
```

Dependencies
------------

- [PyYAML](https://pypi.python.org/pypi/PyYAML/)
- [Unidecode](https://pypi.python.org/pypi/Unidecode)

Copyright
---------

Copyright 2013-2017 Institute of Formal and Applied Linguistics, Charles University, Prague.
Licensed under the Apache 2.0 license (see [LICENSE.txt](LICENSE.txt)).
