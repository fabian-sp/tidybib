# tidybib

A simple script for tidying .bib files. Make sure that [requirements](requirements.txt) are installed. Then run, for example,

	python tidy.py mybibfilename -o outputfilename

You can do a test run with the `test.bib` in this repo using which will add a `test_new.bib`.

	python tidy.py test -a

`mybibfilename` and `outputfilename` do not need the `.bib` extension. There are several options which can isnpected with

	python tidy.py -h

## Functionalities

* Suggests a possible DOI (see below for details)
* Makes DOIs uppercase (DOIs are case insensitive, see [this](https://www.doi.org/doi_handbook/2_Numbering.html#2.4) for more info)

Optional:

* `-a`: sets all below options to True.
* `-ru`: removes field url if a certain substring is contained in it. The substring can be specified with the option `-s`.
* `-tm`: makes arXiv entries of type `Misc`. 
* `-re`: removes field eprint for arXiv entries.
* `-ra`: removes field abstract for arXiv entries.

## Comments on DOI suggestions

The DOI suggestion works as follows: we query the Crossref API with the given **title and author**. The script takes the best match from Crossref and checks whteher the queried title and the title of the best match are similar. If this is the case, the DOI is suggested. Therefore DOI search should **only** be used as a suggestion and **always checked**.

Some random notes/observations:

* Many tasks for cleaning .bib files (e.g. remove duplicates, journal abbreviations) can be done with e.g. Jabref.
* Sometimes when adding a paper from arxiv with Jabref, the correct journal article (e.g. from SIAM) is automatically added. See this [example](https://arxiv.org/abs/1810.05633v2). This is probably due to the fact that the arxiv page has been update with information about the subsequent publication.