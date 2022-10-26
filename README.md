# Clinical Disease Embedding
A project to convert clinical diseases in wikipedia articles to vector embeddings.

# Usage

## Install dependencies

Install all dependencies with pip:
`pip install -r requirements.txt`

## Download wikipedia dumps with

`python -m src.download_wikipedia --path <download_path> --dump-name <dump_name>`

dump_name must be one of the dumps available at: https://dumps.wikimedia.org/enwiki/

Example:
`python -m src.download_wikipedia --path /home/gonzalo/wiki_data --dump-name 20220901`
