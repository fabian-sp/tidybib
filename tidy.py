import sys
import re
from unidecode import unidecode
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
import requests
import urllib
import time

# adapted from https://gist.github.com/jgomezdans/466bb7471685556e7526449bee7a0bfd


class DOIError(Exception):
    pass


def searchdoi(title, authors, tries=4):
    params = urllib.parse.urlencode(
        {"query.author": authors, "query.title": title})
    url_base = "http://api.crossref.org/works?"
    trying = True
    try_count = 0
    while trying and try_count <= tries:
        response = requests.get(url_base + params)
        if response.ok:
            trying = False
            try:
                doi = response.json()['message']['items'][0]['DOI']
            except:
                print("something wrong with json response for " + params)
                raise DOIError
        else:
            try_count += 1
            print("Response not 200 OK. Retrying, try " + str(try_count)
                + " of " + str(tries))
            time.sleep(1)
    if try_count >= tries:
        raise DOIError("Tried more than " + str(tries) + " times. Response"
                    " still not 200 OK! Uh oh...")
    return doi


def normalize(string):
    """Normalize strings to ascii, without latex."""
    string = re.sub(r'[{}\\\'"^]', "", string)
    # better remove all math expressions
    string = re.sub(r"\$.*?\$", "", string)
    return unidecode(string)


def get_authors(entry):
    """Get a list of authors' or editors' last names."""
    def get_last_name(authors):
        for author in authors:
            author = author.strip(" ")
            if "," in author:
                yield author.split(",")[0]
            elif " " in author:
                yield author.split(" ")[-1]
            else:
                yield author

    try:
        authors = entry["author"]
    except KeyError:
        authors = entry["editor"]

    authors = normalize(authors).split("and")
    return list(get_last_name(authors))

def get_doi(entry):
    
    if "doi" not in entry or entry["doi"].isspace():
        title = entry["title"]
        authors = entry["author"]
        try:
            doi = searchdoi(title, authors)
            entry['doi'] = doi.upper()
            print("Added DOI for " + entry['ID'])
            changed = 1
        except DOIError:
            print("Unable to find DOI for " + entry['ID'])
    else:
        if entry['doi'] != entry['doi'].upper():
            entry['doi'] = entry['doi'].upper()
            print("Made DOI uppercase for " + entry['ID'])            
            changed = 1
        else:
            changed = 0
    return changed

def is_arxiv(entry):
    
    opt1 = entry.get('archiveprefix') == 'arXiv'
    opt2 = 'arxiv' in entry['url'] if entry.get('url') else False
    return any([opt1,opt2]) 

def tidy_arxiv(entry, remove_eprint=True, make_misc=False):
    # delete abstract
    if entry.get('abstract'):
        entry.pop('abstract')

    # remove eprint    
    if remove_eprint:
       if entry.get('eprint'):
           entry.pop('eprint')
    
    # make entrytype misc
    if make_misc:
        if entry.get('ENTRYTYPE'):
           entry['ENTRYTYPE'] = 'Misc'
     
    return

UBTUM_ID = 'eaccess.ub.tum'

def tidy_url(entry):
    count = 0
    if entry.get('url'):
        if UBTUM_ID in entry['url']:
            entry.pop('url')
            print("Removed URL for " + entry['ID'])
            count = 1
    return count
    

def main(fname, remove_eprint=True, make_misc=False):
    print("Reading Bibliography...")
    with open(fname+'.bib') as bib_file:
        bib = bibtexparser.bparser.BibTexParser(common_strings=True).parse_file(bib_file)
    
    new_doi = 0
    clean_url = 0
    
    total = len(bib.entries)
    
    for i, entry in enumerate(bib.entries):
        print("\r{i}/{total} entries processed \n".format(i=i, total=total), flush=True, end="")
        
        key = entry['ID']
        
        if entry.get('author') is None:
            print(f'No author for entry {key}. Will be skipped.')
            continue            
        if entry.get('title') is None:
            print(f'No title for entry {key}. Will be skipped.')
            continue            
        
        if is_arxiv(entry):
            tidy_arxiv(entry, remove_eprint, make_misc)
        
        # only search for DOI if not arxiv?
        else:
            count_doi = get_doi(entry)
        
        count_url = tidy_url(entry)
        
        clean_url += count_url
        new_doi += count_doi
        
    print(f"DOIs changed: {new_doi}")
    print(f"URL removed: {clean_url}")
    outfile = fname + "_new.bib"
    print("Writing result to ", outfile)
    writer = BibTexWriter()
    writer.indent = '    '     # indent entries with 4 spaces instead of one
    with open(outfile, 'w') as bibfile:
        bibfile.write(writer.write(bib))

if __name__ == '__main__':
    main(sys.argv[1])