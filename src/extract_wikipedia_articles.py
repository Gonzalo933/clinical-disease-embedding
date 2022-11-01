# Source https://github.com/WillKoehrsen/wikipedia-data-science/blob/master/notebooks/Downloading%20and%20Parsing%20Wikipedia%20Articles.ipynb
import argparse
import gc
import json
import logging
import os
import subprocess
import sys
import xml.sax

# Sending keyword arguments in map
from functools import partial

# List of lists to single list
from multiprocessing import Pool
from pathlib import Path
from timeit import default_timer as timer

import mwparserfromhell
import tqdm

logging.basicConfig(stream=sys.stdout, encoding="utf-8", level=logging.INFO)
log = logging.getLogger("extract_articles")
log.setLevel(logging.INFO)


class WikiXmlHandler(xml.sax.handler.ContentHandler):
    """Parse through XML data using SAX"""

    def __init__(self, infobox_template):
        """Parse through XML data using SAX

        Args:
            infobox_template (_type_): Infobox template name. https://en.wikipedia.org/wiki/Category:Infobox_templates
        """
        xml.sax.handler.ContentHandler.__init__(self)
        self._buffer = None
        self._values = {}
        self._current_tag = None
        self._diseases = []
        self._article_count = 0
        self._non_matches = []
        self.infobox_template = infobox_template

    def characters(self, content):
        """Characters between opening and closing tags"""
        if self._current_tag:
            self._buffer.append(content)

    def startElement(self, name, attrs):
        """Opening tag of element"""
        if name in ("title", "text", "timestamp"):
            self._current_tag = name
            self._buffer = []

    def endElement(self, name):
        """Closing tag of element"""
        if name == self._current_tag:
            self._values[name] = " ".join(self._buffer)

        if name == "page":
            self._article_count += 1
            # Search through the page to see if the page is a book
            disease = process_article(**self._values, template=self.infobox_template)
            # Append to the list of books
            if disease:
                self._diseases.append(disease)


def process_article(title, text, timestamp, template):
    """Process a wikipedia article looking for template"""

    # Create a parsing object
    wikicode = mwparserfromhell.parse(text)

    # Search through templates for the template
    matches = wikicode.filter_templates(matches=template)
    # Filter by text
    # matches = wikicode.filter(matches = 'Infobox medical condition')
    # Filter out errant matches
    # matches = [x for x in matches if x.name.strip_code().strip().lower() == template.lower()]

    if len(matches) >= 1:
        # template_name = matches[0].name.strip_code().strip()

        # Extract information from infobox
        try:
            properties = {
                param.name.strip_code().strip(): param.value.strip_code().strip()
                for param in matches[0].params
                if param.value.strip_code().strip()
            }
        except AttributeError:
            properties = {}
        # Extract internal wikilinks
        wikilinks = [x.title.strip_code().strip() for x in wikicode.filter_wikilinks()]

        # Extract external links
        exlinks = [x.url.strip_code().strip() for x in wikicode.filter_external_links()]

        # Find approximate length of article
        text_length = len(wikicode.strip_code().strip())

        return (title, properties, wikilinks, exlinks, timestamp, text_length)


def find_medical_articles(input_file, output_dir, limit=None, save=True):
    """Find all the medical condition articles from a compressed wikipedia XML dump.
    `limit` is an optional argument to only return a set number of books.
     If save, books are saved to partition directory based on file name"""

    # Create file name based on partition name
    output_file = output_dir / ndjson_file_name(input_file)

    if Path(output_file).is_file():
        # Already processed
        return
    # Object for handling xml
    handler = WikiXmlHandler(infobox_template="Infobox medical condition")

    # Parsing object
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)

    # Iterate through compressed file
    for i, line in enumerate(
        subprocess.Popen(["bzcat"], stdin=open(input_file), stdout=subprocess.PIPE).stdout
    ):
        try:
            parser.feed(line)
        except StopIteration:
            break

        # Optional limit
        if limit is not None and len(handler._diseases) >= limit:
            return handler._diseases

    if save:
        # Open the file
        with open(output_file, "w") as fout:
            # Write as json
            for disease in handler._diseases:
                fout.write(json.dumps(disease) + "\n")

        log.info("%s files processed.", len(os.listdir(output_dir)))

    # Memory management
    del handler
    del parser
    gc.collect()
    return None


def ndjson_file_name(bz2_name):
    """Returns output file name (.ndjson) for a given input (.bz2) file

    Args:
        bz2_name (Path): input file path
    """
    return Path(f"{Path(bz2_name).stem}.ndjson")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download wikipedia dumps")
    parser.add_argument("--download-path", default=Path().absolute() / Path("data") / Path("bz2"))
    parser.add_argument("--output-path", default=Path().absolute() / Path("data") / Path("ndjson"))
    parser.add_argument("--n-cpus", default=6)
    args = parser.parse_args()
    n_cpus = args.n_cpus
    input_path = Path(args.input_path)
    output_path = Path(args.output_path)

    if not os.path.exists(input_path):
        log.error("Missing input path %s", input_path)
        sys.exit(1)
    Path(output_path).mkdir(parents=True, exist_ok=True)
    # Get all files to parse
    bz2_partitions = [f for f in input_path.glob("*.bz2") if "xml-p" in f.name]
    # Remove processed bz2_partitions
    bz2_partitions = [
        p for p in bz2_partitions if not (output_path / ndjson_file_name(p)).is_file()
    ]
    # enwiki-20220901-pages-articles-multistream27.xml-p71475910p71655058.bz2
    # enwiki-20220901-pages-articles27.xml-p71475910p71655058.bz2
    start = timer()
    pool = Pool(processes=n_cpus)
    results = []
    log.debug([p.name for p in bz2_partitions])
    # Run bz2_partitions in parallel
    for x in tqdm.tqdm(
        pool.imap_unordered(
            partial(find_medical_articles, output_path=output_path), bz2_partitions
        ),
        total=len(bz2_partitions),
    ):
        results.append(x)

    pool.close()
    pool.join()

    end = timer()
