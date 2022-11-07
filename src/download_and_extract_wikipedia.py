"""
This is a mix from the code in
download_wikipedia.py
and
extract_wikipedia_articles.py

This code downloads a extracts each file in a iterative way. Then removes the .bz2 file. The result is a folder with the ndjson but using only space for a single .bz2.
It is mean to be used in systems with low HDD space.
"""
import argparse
import logging
import os
import sys

# Sending keyword arguments in map
from functools import partial

# List of lists to single list
from multiprocessing import Pool
from pathlib import Path
from timeit import default_timer as timer

import tqdm

from .download_wikipedia import WikipediaDownloader
from .extract_wikipedia_articles import find_medical_articles, ndjson_file_name

logging.basicConfig(stream=sys.stdout, encoding="utf-8", level=logging.INFO)
log = logging.getLogger("download_and_extract")
log.setLevel(logging.INFO)


def download_and_process(f, output_path, remove_bz2_after_download=True):
    # Check if ndjson exists
    if (output_path / ndjson_file_name(f)).is_file():
        log.info("Skip %s", output_path / ndjson_file_name(f))
        return
    downloaded_path, info = wikipedia_downloader.download_wikipedia_file(f)
    log.info("Downloaded %s", downloaded_path)
    find_medical_articles(downloaded_path, output_path)
    if remove_bz2_after_download:
        log.info("Removing %s", downloaded_path)
        downloaded_path.unlink(missing_ok=True)
    return output_path / ndjson_file_name(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download wikipedia dumps")
    parser.add_argument("--download-path", default=Path().absolute() / Path("bz2"))
    parser.add_argument("--dump-name", default="20220901")
    parser.add_argument("--output-path", default=Path().absolute() / Path("data") / Path("ndjson"))
    parser.add_argument("--n-cpus", default=6)

    args = parser.parse_args()
    download_dir = Path(args.download_path)
    log.info("Downloading data to %s", download_dir)
    args = parser.parse_args()
    n_cpus = int(args.n_cpus)
    output_path = Path(args.output_path)
    dump_name = args.dump_name
    Path(output_path).mkdir(parents=True, exist_ok=True)

    wikipedia_downloader = WikipediaDownloader(download_dir, dump_name)
    files_to_download = wikipedia_downloader.get_dump_file_names()
    data_paths = []
    file_info = []
    start = timer()
    pool = Pool(processes=n_cpus)
    results = []
    # Iterate through each file
    for x in tqdm.tqdm(
        pool.imap_unordered(
            partial(download_and_process, output_path=output_path), files_to_download
        ),
        total=len(files_to_download),
    ):
        results.append(x)
    pool.close()
    pool.join()

    end = timer()
