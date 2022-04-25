import sys
import os
import re
from unidecode import unidecode
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
import requests
import urllib
import time
from difflib import SequenceMatcher
import argparse

# adapted from https://gist.github.com/jgomezdans/466bb7471685556e7526449bee7a0bfd


parser = argparse.ArgumentParser(description='Tidy your bib file.')

parser.add_argument('fname', type=str, help="filename of the bib file (without .bib)")
parser.add_argument('-o', '--output_name', nargs='?', type=str, default = None,\
                    help="filename of the output (without .bib). If not specified, set to <fname>_new")


parser.add_argument('-a', '--all', help="activate all options", action="store_true")
parser.add_argument('-tm', '--to_misc', help="make arxiv entries to type Misc", action="store_true")
parser.add_argument('-re', '--eprint_removed', help="remove field eprint for arxiv entries", action="store_true")
parser.add_argument('-ra', '--abstract_removed', help="remove field abstract for arxiv entries", action="store_true")
parser.add_argument('-ru', '--url_deleted', help="delete url entry whenever a substring is contained. See option -s", action="store_true")
parser.add_argument('-s', '--substring', nargs='?', type=str, default='eaccess.ub.tum',\
                    help="substring in URL that leads to deletion")

args = parser.parse_args()

# if no output file --> store as _old and overwrite
if args.output_name is None:
    rename_to_old = True
    args.output_name = args.fname
else:
    rename_to_old = False
    
# all option
if args.all:
    args.to_misc = True
    args.eprint_removed = True
    args.abstract_removed = True
    args.url_deleted = True
    

#print(args)

#%%
empty_print = '   '

class DOIError(Exception):
    pass

def searchdoi(title, authors, tries=4, min_score=0.8):
    params = urllib.parse.urlencode({"query.author": authors, "query.title": title})
    url_base = "http://api.crossref.org/works?"
    trying = True
    try_count = 0
    while trying and try_count <= tries:
        response = requests.get(url_base + params)
        if response.ok:
            trying = False
            try:
                best_match = response.json()['message']['items'][0]
                # compute similarity of titles
                match_prob = SequenceMatcher(None,title,best_match['title'][0]).ratio()
                
                if match_prob >= min_score:    
                    doi = best_match['DOI'].upper()
                else:
                    doi = None
            except:
                print("something wrong with json response for " + params)
                raise DOIError
        else:
            try_count += 1
            print("Response not 200 OK. Retrying, try " + str(try_count) + " of " + str(tries))
            time.sleep(1)
            
    if try_count >= tries:
        raise DOIError("Tried more than " + str(tries) + " times. Response still not 200 OK!")
        
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
    doi = None # only changed when there is a suggestion
    if "doi" not in entry or entry["doi"].isspace():
        title = entry["title"]
        authors = entry["author"]
        try:
            doi = searchdoi(title, authors)
            if doi is not None:
                print(empty_print + f"Suggested DOI for {entry['ID']}:", doi)
            changed = 0
        except DOIError:
            changed = 0
            
    else:
        if entry['doi'] != entry['doi'].upper():
            entry['doi'] = entry['doi'].upper()
            print(empty_print + "Made DOI uppercase for " + entry['ID'])            
            changed = 1
        else:
            changed = 0
            
    return changed, doi

def is_arxiv(entry):    
    opt1 = entry.get('archiveprefix') == 'arXiv'
    opt2 = 'arxiv' in entry['url'] if entry.get('url') else False
    return any([opt1,opt2]) 

def tidy_arxiv(entry):
    # delete abstract
    if args.abstract_removed:
        if entry.get('abstract'):
            entry.pop('abstract')

    # remove eprint    
    if args.eprint_removed:
       if entry.get('eprint'):
           entry.pop('eprint')
    
    # make entrytype misc
    if args.to_misc:
        if entry.get('ENTRYTYPE'):
           entry['ENTRYTYPE'] = 'Misc'
     
    return

def tidy_url(entry):
    count = 0
    if entry.get('url'):
        if args.substring in entry['url']:
            entry.pop('url')
            print("Removed URL for " + entry['ID'])
            count = 1
    return count


def main(fname):
    print("Reading Bibliography...")
    with open(fname+'.bib') as bib_file:
        bib = bibtexparser.bparser.BibTexParser(common_strings=True).parse_file(bib_file)
    
    # initialize
    change_doi = 0
    clean_url = 0
    suggest_dois = list()
    
    total = len(bib.entries)
    
    for i, entry in enumerate(bib.entries):
        print(f'--{i}/{total}-- processing entry', entry['ID'])
        key = entry['ID']
        
        if entry.get('author') is None:
            print(empty_print + f'No author for entry {key}. Will be skipped.')
            continue            
        if entry.get('title') is None:
            print(empty_print + f'No title for entry {key}. Will be skipped.')
            continue            
        
        if is_arxiv(entry):
            tidy_arxiv(entry)
        
        count_doi, this_doi = get_doi(entry)
        if this_doi is not None:
            suggest_dois.append(f"Suggested DOI for {entry['ID']}: {this_doi}")
        
        if args.url_deleted:
            count_url = tidy_url(entry)
        else:
            count_url = 0
            
        clean_url += count_url
        change_doi += count_doi
        
    print("\n\n\n")
    print("-------------- SUMMARY --------------")
    for s in suggest_dois:
        print(s + "\n")
        
    print(f"DOIs changed to uppercase: {change_doi}")
    print(f"URL removed: {clean_url}")
    
    # rename old file
    if rename_to_old:
        os.rename(args.fname+'.bib', args.fname+'_old'+'.bib')
    
    # write new file
    outfile = args.output_name+'.bib'
    print("Writing result to ", outfile)
    writer = BibTexWriter()
    writer.indent = '    '     # indent entries with 4 spaces instead of one
    with open(outfile, 'w') as bibfile:
        bibfile.write(writer.write(bib))
        
#%%

if __name__ == '__main__':
    main(args.fname)