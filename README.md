# Bibpaepr: Cite the paper in a proper way

When we cite other scholars' papers, we often find that most of the articles searched by Google Scholar cite arxiv's preprint Bibtex (even if this paper has been __PUBLISHED__  in some journals or conferences), which makes our paper writing appear unprofessional. I wrote an automated script&exe __Bibpaper__ that can find what conference the paper has been cited by and return the response of the latest citation.

All you need to do is enter the title of the article and click Fetch Bibtex to get the Bibtex of the paper.

## News 
:sun_with_face: I published Bibpaper version==0.1 

## How to use it?    
![image](https://github.com/user-attachments/assets/b4bec08e-c794-4efb-85ae-17a72eb5f6b3)

Here you can find this paper has been included in ICLR 2024 :tada:

![image](https://github.com/user-attachments/assets/bb29dc47-c482-47a3-890c-426a550a14ae)

However,if you search for this paper directly in Google,you will find it still in arxiv version
## Installation

```bash
git clone 
```

OR

```bash
git clone https://github.com/yuchenlin/rebiber.git
cd rebiber/
pip install -e .
```
If you would like to use the latest github version with more bug fixes, please use the second installation method.

## Usage（v1.1.3 and v1.2.0）
Normalize your bibtex file with the official conference information:

```bash 
rebiber -i /path/to/input.bib -o /path/to/output.bib
```
You can find a pair of example input and output files in `rebiber/example_input.bib` and `rebiber/example_output.bib`.

| argument | usage|
| ----------- | ----------- |
| `-i` | or `--input_bib`.  The path to the input bib file that you want to update |
| `-o` | or `--output_bib`.  The path to the output bib file that you want to save. If you don't specify any `-o` then it will be the same as the `-i`. |
| `-r` | or `--remove`. A comma-separated list of value names that you want to remove, such as "-r pages,editor,volume,month,url,biburl,address,publisher,bibsource,timestamp,doi". Empty by __default__.  |
| `-s` | or `--shorten`. A bool argument that is `"False"` by __default__, used for replacing `booktitle` with abbreviation in `-a`. Used as `-s True`. |
| `-d` | or `--deduplicate`. A bool argument that is `"True"` by __default__, used for removing the duplicate bib entries sharing the same key. Used as `-d True`. |
| `-l` | or `--bib_list`. The path to the list of the bib json files to be loaded. Check [rebiber/bib_list.txt](rebiber/bib_list.txt) for the default file. Usually you don't need to set this argument. |
| `-a` | or `--abbr_tsv`. The list of conference abbreviation data. Check [rebiber/abbr.tsv](rebiber/abbr.tsv) for the default file. Usually you don't need to set this argument. |
| `-u` | or `--update`. Update the local bib-related data with the latest Github version. |
| `-v` | or `--version`. Print the version of current Rebiber. |
| `-st` | or `--sort`. A bool argument that is `"False"` by __default__. used for keeping the original order of the bib entries of the input file. By setting it to be `"True"`, the bib entries are ordered alphabetically in the output file. Used as `-st True`. |

<!-- Or 
```bash
python rebiber/normalize.py \
  -i rebiber/example_input.bib \
  -o rebiber/example_output.bib \
  -l rebiber/bib_list.txt
``` -->


##By the way
Don't hesitate to leave your :star2: 

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yuchenlin/rebiber&type=Date)](https://star-history.com/#yuchenlin/rebiber&Date)

## Contact

Please email yuchen.lin@usc.edu or create Github issues here if you have any questions or suggestions. 
