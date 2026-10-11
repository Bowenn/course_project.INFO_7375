"""Custom Dataset Builder for Common Crawl."""
import time

import datasets
import homework 
import utils
from typing import List, Iterator, Tuple, Dict, Any

logger = datasets.logging.get_logger(__name__)

_DESCRIPTION = "A shard of the Common Crawl dataset."
_DATA_URL = "https://data.commoncrawl.org/crawl-data/CC-MAIN-2018-17/segments/1524125937193.1/warc/CC-MAIN-20180420081400-20180420101400-00000.warc.gz" 
 
class MiniCleanedCommonCrawl(datasets.GeneratorBasedBuilder):
    def _info(self) -> datasets.DatasetInfo:
        """
        Should return a DatasetInfo object describing <string> type values for a url and it's corresponding text.
        """
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features({
                "url": datasets.Value("string"),
                "text": datasets.Value("string")
            })
        )

    def _split_generators(self, dl_manager: datasets.DownloadManager) -> List[datasets.SplitGenerator]:
        """
        Should return a SplitGenerator object which downloads your data and creates train and validation splits.
        """
        downloaded_file = dl_manager.download(_DATA_URL)
        return [datasets.SplitGenerator(
            name=datasets.Split.TRAIN, # type: ignore
            gen_kwargs={
                "filepaths": [downloaded_file]
            }
        ),]
    
    def _generate_examples(self, filepaths: List[str]) -> Iterator[Tuple[Any, Dict[str, str]]]:
        """
        Streams raw data from the downloaded file and yields tuples consisting of a unique ID and the url/cleaned text.
        Should call the functions you defined in homework.py. 
        """
        seen = 0
        passes = 0
        for filepath in filepaths:
            # Note: Replace 'read_warc' with the actual function from your homework/utils that yields records
            records = utils.read_warc_file(filepath, 900) 
            
            for index, (url, html_text) in enumerate(records):
                seen += 1
                try:
                    text = homework.html_to_text(html_text)
                except Exception as e:
                    print(f"Error converting HTML to string: {e}")
                    continue
                # print("\n\n\nAfter HTML to text: ", text)
                cleaned_text = homework.clean_text(text)
                # print("After cleaning: ", cleaned_text)
                cleaned_nopii_text = homework.replace_pii(cleaned_text)
                # print("After PII removal: ", cleaned_nopii_text)
                passes_check = homework.heuristic_quality_filter(cleaned_nopii_text)
                # print(url)
                # print("Passes heuristic quality filter:", passes_check)
                if passes_check:
                    passes += 1
                    yield index, {
                        "url": url,
                        "text": cleaned_nopii_text
                    }
        print(f"{passes} passed out of {seen} records processed.")
 
if __name__ == "__main__":   
    # Note: Calling load_dataset caches the processed dataset locally.
    # The default cache directory is ~/.cache/huggingface/datasets.
    # To force the dataset to be recreated, you should pass in the
    # additional argument download_mode=datasets.DownloadMode.REUSE_CACHE_IF_EXISTS
    dataset = datasets.load_dataset(
        "mini_ccc.py",
        "MiniCleanedCommonCrawl",
        trust_remote_code=True,
        split=datasets.Split.TRAIN) # type: ignore
    
    # Iterate over the first 100 examples.
    for ex in dataset.take(100):
        print(ex["url"])