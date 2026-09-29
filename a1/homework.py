import argparse
import re
import requests
import json
from utils import  read_warc_file, read_wet_file
from datasets import load_dataset
from typing import Set, Dict
import string
from bs4 import BeautifulSoup


def retrieve_bad_words(bad_word_file: str) -> set[str]:
    """Helper function - that reads a list of bad words from a file and returns them as a set.
    Returns:
        Set[str]: A set containing lowercase bad words.
    """
    with open(bad_word_file, 'r') as file:
        records = file.read().strip().split('\n')
        bad_words = [record.lower() for record in records]
        return set(bad_words)

def html_to_text(html: str) -> str:
    """Converts HTML content to plain text..
    Args:
        html (str): HTML content as a string.
    Returns:
        str: Plain text extracted from HTML.
    """
    soup = BeautifulSoup(html, 'html.parser')
    for element in soup(['script', 'style']):
        element.decompose()

    # Extract the remaining text
    return soup.get_text(separator='\n', strip=True)

REGEX_PATTERNS = {
    # 'email': {
    #     'reg': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    #     'into': '[EMAIL]'
    # },
    'phone': {
        # 'reg': r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
        'reg': r'(\+1 ?)\d{3}([-.\s]?)\d{3}([-.\s]?)\d{4}\b',
        'into': lambda m: f"{m.group(1)}XXX{m.group(2)}XXX{m.group(3)}XXXX"
    },
    'ssn': {
        'reg': r'\b\d{3}-\d{2}-\d{4}\b',
        'into': 'XXX-XX-XXXX'
    },
    # 'credit_card': {
    #     'reg': r'\b(?:\d[ -]*?){13,16}\b',
    #     'into': '[CREDIT_CARD]'
    # },
    # 'ip_address': {
    #     'reg': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    #     'into': '[IP_ADDRESS]'
    # },
    # 'url': {
    #     'reg': r'\b(?:https?://|www\.)[^\s]+\b',
    #     'into': '[URL]'
    # }
}

def replace_pii(text: str) -> str:
    """Masks personally identifiable information (PII) from text with the specified masking formats.
    Args: 
        text (str): Candidate text.
    Returns:
        str: Text with PII obfuscated.
    """
    for pii_type, pattern in REGEX_PATTERNS.items():
        text = re.sub(pattern['reg'], pattern['into'], text)
    return text


def clean_text(text: str) -> str:
    """Removes substrings identified as low-quality according to alphanumeric, whitespace and valid document checks.  
    Args:
        text (str): document to process.
    Returns:
        str: cleaned document
    """
    def filter(p):
        return len(p) > 0 \
            and not re.search(r'(?:(?!_)\w){101,}', p) \
            and any(c in string.punctuation for c in p)
    
    paragraphs = text.split('\n')
    cleaned_paragraphs = [p for p in paragraphs if filter(p)]
    return '\n'.join(cleaned_paragraphs)


def heuristic_quality_filter(text: str, bad_words_set: set) -> bool:
    """Rejects documents based on the presence of bad words and punctuation.
    Args:
        text (str): document to check
    Returns:
        bool: returns True if the document passes the filters, False otherwise.
    """
    # Condition 3 first: non-whitespace characters (this also protects condition 4 from dividing by zero)
    if len(text.strip()) == 0:
        return False

    # Condition 1: no bad words (decide: word-level or substring matching?)
    lower_text = text.lower()
    if any(bad_word in lower_text for bad_word in bad_words_set):
        return False

    # Condition 2: contains at least one punctuation character (reuse your clean_text logic)
    if not any(c in string.punctuation for c in text):
        return False

    # Condition 4: at least 80% of characters are alphanumeric, punctuation, or whitespace
    total_chars = len(text)
    valid_chars = sum(1 for c in text if c.isalnum() or c in string.punctuation or c.isspace())

    if valid_chars / total_chars < 0.8:
        return False

    return True

def deduplicate_texts(texts: list[str]) -> list[str]:
    """Deduplicates text by removing duplicate sentences.
    Args:
        text (str): Text to deduplicate.
    Returns:
        str: Deduplicated text. Implemented a simple Jaccard similarity based deduplication. 
    """
    unique_texts: list[str] = []
    unique_texts_sets: list[set[str]] = []
    for text in texts:
        text_set = set(re.split(r'[ ,.!?()";:]+', text.lower()))
        is_duplicate = False
        for unique_set in unique_texts_sets:
            intersection = text_set & unique_set
            union = text_set | unique_set
            similarity = len(intersection) / len(union) if union else 0
            if similarity > 0.8:  # Threshold for considering as duplicate
                is_duplicate = True
                break
        if not is_duplicate:
            unique_texts_sets.append(text_set)
            unique_texts.append(text)
    return unique_texts


if __name__ == '__main__' :
    parser = argparse.ArgumentParser()
    parser.add_argument('--fname', type = str,  default = 'dataset/data.warc', help = 'Specify the path for your warc file.')
    parser.add_argument('--dfname', type = str,  default = 'topic_dataset.json', help = 'Specify the path where you stored topic_dataset.json')
    parser.add_argument('--bfname', type = str,  default = 'bad_word_list.txt', help = 'Specify the path where you stored bad_word_list.txt')
    parser.add_argument('--num_records', type = int,  default = 30, help = 'Specify the number of records you want to parse (only used for debugging with smaller sets)')
    parser.add_argument('--wet_name', type = str, default = 'dataset/data.wet', help = 'Specify the path for your wet file.')
    parser.add_argument('--wat_name', type = str, default = 'dataset/data.wat', help = 'Specify the path for your wat file.')
    args = parser.parse_args()

    bad_words_set = retrieve_bad_words(args.bfname)

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
            passes_check = heuristic_quality_filter(cleaned_nopii_text, bad_words_set)
            print(url)
            print("Passes heuristic quality filter:", passes_check)
            if passes_check:
                passes += 1
                # print(cleaned_nopii_text)
                print("\n\n")
        print(f"{passes} passed out of {seen} records processed.")

    if args.dfname:
        with open(args.dfname, 'r') as f:
            raw_texts = json.load(f)
        raw_texts = [item['text'] for item in raw_texts['data']]
        deduplicated_texts = deduplicate_texts(raw_texts)
        print(f"Deduplicated {len(raw_texts)} texts to {len(deduplicated_texts)} unique texts.")
        
    else:
        print("Usage: python homework.py --fname data.warc")