
from utils import  read_warc_file, read_wet_file

if __name__ == '__main__':
    iterator = read_wet_file('./dataset/data.wet', num_to_read=10)
    for url, text in iterator:
        print(f"URL: {url}")
        print(f"Text: {text.decode('utf-8')[:200]}...")  # Print first 200 characters of text
        print("\n")