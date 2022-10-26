# Source https://github.com/WillKoehrsen/wikipedia-data-science/blob/master/notebooks/Downloading%20and%20Parsing%20Wikipedia%20Articles.ipynb
import argparse
import logging

# File system management
import os
import sys
from pathlib import Path

import requests

# Parsing HTML
from bs4 import BeautifulSoup
from keras.utils import get_file

logging.basicConfig(stream=sys.stdout, encoding="utf-8", level=logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class WikipediaDownloader:
    base_url = "https://dumps.wikimedia.org/enwiki/"

    def __init__(self, download_dir, dump_name):
        self.download_dir = download_dir if isinstance(download_dir, Path) else Path(download_dir)
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
        self.dump_name = dump_name if args.dump_name[-1] == "/" else args.dump_name + "/"
        self.dump_url = self.base_url + self.dump_name
        log.info("dump_name: %s", dump_name)

    def get_dump_file_names(self):
        # List all wikipedia dumps and get the most recent
        index = requests.get(self.base_url).text
        soup_index = BeautifulSoup(index, "html.parser")

        # Find the links that are dates of dumps
        dumps = [a["href"] for a in soup_index.find_all("a") if a.has_attr("href")]
        log.debug("Available Dumps: %s", dumps)

        # Retrieve the html
        dump_html = requests.get(self.dump_url).text
        # Convert to a soup
        soup_dump = BeautifulSoup(dump_html, "html.parser")
        files = []
        # Search through all files
        for f in soup_dump.find_all("li", {"class": "file"}):
            text = f.text
            # Select the relevant files
            if "pages-articles" in text:
                files.append((text.split()[0], text.split()[1:]))

        files_to_download = [f[0] for f in files if ".xml-p" in f[0]]
        log.debug("Files %s", files_to_download)
        log.info("Found %d files", len(files_to_download))
        if len(files_to_download) == 0:
            log.warning(
                "No dump files found. Make sure that 'dump_name' is one of: %s. Available at %s",
                dumps,
                self.base_url,
            )
        return files_to_download

    def download_wikipedia_backup(self):
        files_to_download = self.get_dump_file_names()
        data_paths = []
        file_info = []

        # Iterate through each file
        for f in files_to_download:
            path = self.download_dir / Path(f)
            file_url = f"{self.dump_url}/{f}"
            log.info("Checking %s", file_url)
            log.info("Output path %s", path)
            # Check to see if the file is already downloaded
            if not os.path.exists(download_dir + f):
                log.info("Downloading file %s", file_url)
                data_paths.append(get_file(f, file_url, cache_subdir=download_dir))
                # Find the file size in MB
                file_size = os.stat(path).st_size / 1e6
                # Find the number of articles
                file_articles = int(f.split("p")[-1].split(".")[-2]) - int(f.split("p")[-2])
                file_info.append((f, file_size, file_articles))
            else:
                # If the file is already downloaded find some information
                data_paths.append(path)
                # Find the file size in MB
                file_size = os.stat(path).st_size / 1e6

                # Find the number of articles
                file_number = int(f.split("p")[-1].split(".")[-2]) - int(f.split("p")[-2])
                file_info.append((f.split("-")[-1], file_size, file_number))
            log.info("Total Wikipedia size: %d", sum([i[1] for i in file_info]))
            log.info("Total Articles: %d", sum([i[2] for i in file_info]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download wikipedia dumps")
    parser.add_argument("--path", default=Path().absolute() / Path("data"))
    parser.add_argument("--dump-name", default="20220901")

    args = parser.parse_args()
    download_dir = args.path
    log.info("Downloading data to %s", download_dir)
    dump_name = args.dump_name
    WikipediaDownloader(download_dir, dump_name).download_wikipedia_backup()
