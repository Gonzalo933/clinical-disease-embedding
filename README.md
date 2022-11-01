# Clinical Disease Embedding
A project to convert clinical diseases in wikipedia articles to vector embeddings.

# Usage

## Install dependencies

Install all dependencies with pip:
`pip install -r requirements.txt`

Bzcat is also required. https://command-not-found.com/bzcat

## Download wikipedia dumps with

`python -m src.download_wikipedia --download-path <download_path> --dump-name <dump_name>`

dump_name must be one of the dumps available at: https://dumps.wikimedia.org/enwiki/

Example:
`python -m src.download_wikipedia --download-path /home/gonzalo/wiki_data/bz2 --dump-name 20220901`
