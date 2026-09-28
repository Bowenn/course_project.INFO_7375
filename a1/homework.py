import argparse
import re
import requests
import json
from utils import  read_warc_file, read_wet_file
from datasets import load_dataset
from typing import Set, Dict
import string

def retrieve_bad_words() -> set[str]:
    """Helper function - that reads a list of bad words from a file and returns them as a set.
    Returns:
        Set[str]: A set containing lowercase bad words.
    """
    with open('./bad_word_list.txt', 'r') as file:
        records = file.read().strip().split('\n')
        bad_words = [record.lower() for record in records]
        return set(bad_words)


def html_to_text(html: str) -> str:
    """Converts HTML content to plain text..
    Args:
        html (bytes): HTML content as bytes.
    Returns:
        str: Plain text extracted from HTML.
    """
    pass 

def replace_pii(text: str) -> str:
    """Masks personally identifiable information (PII) from text with the specified masking formats.
    Args: 
        text (str): Candidate text.
    Returns:
        str: Text with PII obfuscated.
    """
    pass 
    

def clean_text(text: str) -> str:
    """Removes substrings identified as low-quality according to alphanumeric, whitespace and valid document checks.  
    Args:
        text (str): document to process.
    Returns:
        str: cleaned document
    """
    pass


def heuristic_quality_filter(text: str) -> bool:
    """Rejects documents based on the presence of bad words and punctuation.
    Args:
        text (str): document to check
    Returns:
        bool: returns True if the document passes the filters, False otherwise.
    """
    pass 
    

def deduplicate_texts(texts: list[str]) -> list[str]:
    """Deduplicates text by removing duplicate sentences.
    Args:
        text (str): Text to deduplicate.
    Returns:
        str: Deduplicated text. Implemented a simple Jacard similarity based deduplication. 
    """
    pass


if __name__ == '__main__' :
    parser = argparse.ArgumentParser()
    parser.add_argument('--fname', type = str,  default = 'dataset/data.warc', help = 'Specify the path for your warc file.')
    parser.add_argument('--dfname', type = str,  default = 'dataset/topic_dataset.json', help = 'Specify the path where you stored topic_dataset.json')
    parser.add_argument('--num_records', type = int,  default = 10, help = 'Specify the number of records you want to parse (only used for debugging with smaller sets)')
    parser.add_argument('--wet_name', type = str, default = 'dataset/data.wet', help = 'Specify the path for your wet file.')
    parser.add_argument('--wat_name', type = str, default = 'dataset/data.wat', help = 'Specify the path for your wat file.')
    args = parser.parse_args()

    if args.fname:
        seen = 0
        passes = 0
        for url, html_text in read_warc_file(args.fname, args.num_records):
            seen += 1

            # print("Before HTML to text: ", str(html_text))
            text = html_to_text(str(html_text))

            # print("\n\n\nAfter HTML to text: ", text)
            cleaned_text = clean_text(text)

            # print("After cleaning: ", cleaned_text)
            cleaned_nopii_text = replace_pii(cleaned_text)

            # print("After PII removal: ", cleaned_nopii_text)
            passes_check = heuristic_quality_filter(cleaned_nopii_text)

            print(url)
            print("Passes heuristic quality filter:", passes_check)
            if passes_check:
                passes += 1
                print(cleaned_nopii_text)
                print("\n\n")
        print(f"{passes} passed out of {seen} records processed.")

    if args.dfname:
        with open(args.dfname, 'r') as f:
            raw_texts = json.load(f)
        raw_texts = [item['text'] for item in raw_texts['data']]
        deduplicated_texts = deduplicate_texts(raw_texts)
        
    else:
        print("Usage: python homework.py --fname data.warc")