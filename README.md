# tidybib
A script for tidying bib files


## Functionalities

* Suggests a possible DOI (see below for details)
* Makes DOIs uppercase

* `-m`: makes arxiv entries of type `Misc` 
* `u`: removes field url if a certain substring is contained in it
* `e`: removes field eprint for arxiv entries
* `a`: removes field abstract for arxiv entries



## Comments on DOI suggestions

The DOI suggestion works as follows: we query the Crossref API with the given **title and author**. The script takes the best match from Crossref and checks whteher the queried title and the title of the best match are similar. If this is the case, the DOI is suggested. Therefore DOI search should **only** be used as a suggestion and **always checked**.

Some insights:
* Sometimes when adding a paper from arxiv (using Jabref), it automatically adds the correct journal article (e.g. from SIAM). Example: Asi, Duchi Aprox. Might be due to the fact that the info about publishing is feeded in arxiv.