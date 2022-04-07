# tidybib
A script for tidying bib files

DOI extraction must be checked for arxiv entries --> it gives incorrect results in current state

Some insights:

* crossref api returns only the best mathces: ie if there is no exact match, the first results will be incorrect. Therefore DOI search should **only** be used as a suggestion.
* Sometimes when adding a paper from arxiv (using Jabref), it automatically adds the correct journal article (e.g. from SIAM). Example: Asi, Duchi Aprox. Might be due to the fact that the info about publishing is feeded in arxiv.