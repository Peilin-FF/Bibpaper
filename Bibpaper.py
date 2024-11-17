import sys
import time
import threading
import requests
import re
import tkinter as tk
from tkinter import scrolledtext
from urllib import parse
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import queue  
from ttkbootstrap import Style
import pyperclip 
import bibtexparser
from xml.etree import ElementTree 

def paperUrl(name):
    q = name
    params = {
        'q': q
    }
    params = parse.urlencode(params)
    url = "https://scholar.google.com/scholar?" + params
    return url

def getBib(url):
    # Set up Firefox browser (remove headless mode for debugging)
    options = Options()
    options.add_argument('--headless')  # Comment out this line for debugging

    # Start Firefox WebDriver
    driver = webdriver.Firefox(options=options)
    
    # Open Google Scholar page
    driver.get(url)
    print("Open Google Scholar page")
    
    try:
        # Wait for the 'Cite' button to be clickable, then click it
        cite_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'gs_or_cit.gs_nph'))
        )
        print("Found Cite button")
        cite_button.click()

        # Wait for the BibTeX link to appear
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'gs_citi'))
        )
        print("Found BibTeX link")

        # Get the BibTeX link and visit it
        s = driver.find_element(By.CLASS_NAME, 'gs_citi')
        if s.text == 'BibTeX':
            hr = s.get_attribute('href')
            driver.get(hr)
            time.sleep(2)
            
            # Get the BibTeX citation text
            bib = driver.find_element(By.XPATH, "//*").text
            print("Fetched BibTeX citation")
    except Exception as e:
        #print(f"Error: {e}")
        bib = None
    
    # Close the browser
    driver.quit()
    return bib


def fetch_arxiv_metadata(query, max_results=1):
    """
        get metadate from arxiv
    """
    base_url = 'https://export.arxiv.org/api/query'
    params = {
        'search_query': query,
        'start': 0,
        'max_results': max_results
    }
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data from arXiv: {response.status_code}")

    # xml response
    root = ElementTree.fromstring(response.content)
    metadata_list = []

    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        metadata = {
            'title': entry.find('{http://www.w3.org/2005/Atom}title').text.strip(),
            'authors': ', '.join(
                author.find('{http://www.w3.org/2005/Atom}name').text
                for author in entry.findall('{http://www.w3.org/2005/Atom}author')
            ),
            'summary': entry.find('{http://www.w3.org/2005/Atom}summary').text.strip(),
            'published': entry.find('{http://www.w3.org/2005/Atom}published').text,
            'arxiv_id': entry.find('{http://www.w3.org/2005/Atom}id').text.split('/')[-1],
            'category': entry.find('{http://arxiv.org/schemas/atom}primary_category').attrib['term'],
            'doi': entry.find('{http://arxiv.org/schemas/atom}doi').text if entry.find('{http://arxiv.org/schemas/atom}doi') is not None else None
        }
        metadata_list.append(metadata)
    
    return metadata_list

def fetch_bibtex_from_arxiv(arxiv_id):
    """
    Fetch the corresponding BibTeX entry from arXiv using its ID.
    
    Parameters:
    - arxiv_id: str, the numerical ID part of an arXiv document, e.g., "2001.09678".
    
    Returns:
    - response.text: the fetched BibTeX data.
    """
    bibtex_url = f'https://arxiv.org/bibtex/{arxiv_id}'
    response = requests.get(bibtex_url)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch BibTeX data: {response.status_code}")
    
    return response.text


def generate_bibtex_key(entry):
    # Extract author, year, title
    author = entry.get('author', '')
    year = entry.get('year', '')
    title = entry.get('title', '')

    if author:
        # Ensure authors are separated by commas
        author_list = author.replace(' and ', ', ').split(', ')  # Replace 'and' with comma separation 
        first_author = author_list[0].strip().split()[0].lower()  # Get first author's surname in lowercase
    else: 
        first_author = 'unknown'
    
    # Get the first word of the title and remove everything after a colon, keeping only alphabetic characters
    if title:
        # Remove part after colon (if any)
        title = title.split(':')[0]  
        # Retain only alphabetic characters and convert to lowercase
        first_word_title = re.sub(r'[^a-zA-Z]', '', title.split()[0].lower())  
    else:
        first_word_title = 'untitled'

    # Generate BibTeX key format: author's surname + year + first word of title
    return f"{first_author}{year}{first_word_title}"

def update_bibtex_entry(bibtex_entry):
    # Parse the BibTeX entry
    bib_database = bibtexparser.loads(bibtex_entry)
    entry = bib_database.entries[0]

    # Ensure the entry type is valid
    entry_type = entry.get('ENTRYTYPE', '').lower()

    # Automatically fix author field by replacing 'and' with commas
    if 'author' in entry: 
        entry['author'] = entry['author'].replace(' and ', ', ') 

    # Automatically add publisher field (default to IEEE if not present)
    if 'publisher' not in entry:
        entry['publisher'] = '' if entry_type in ['inproceedings', 'article'] else ''
    
    # Automatically add url field if DOI exists
    if 'doi' in entry and 'url' not in entry:
        entry['url'] = f"https://doi.org/{entry['doi']}"

    # Ensure volume and number fields are included (if missing, leave them empty)
    entry.setdefault('volume', '')
    entry.setdefault('number', '')

    # Generate the BibTeX key
    bibtex_key = generate_bibtex_key(entry)

    # Update the BibTeX entry with the generated key
    entry['ID'] = bibtex_key

    # Format and align the output
    formatted_entry = f"@{entry_type}{{{entry['ID']},\n"
    
    # Format and align fields
    for field, value in entry.items():
        if field != 'ID' and field != 'ENTRYTYPE':
            formatted_entry += f"  {field: <15} = {{{value}}},\n"

    formatted_entry = formatted_entry.rstrip(',\n') + "\n}"

    # Return the updated BibTeX entry
    return formatted_entry


def bibtex_to_custom_format(bibtex_entry):
    # Parse the BibTeX entry
    bib_database = bibtexparser.loads(bibtex_entry)
    entry = bib_database.entries[0]

    # Get entry type
    entry_type = entry.get('ENTRYTYPE', '').lower()

    # Get author list
    authors = entry.get('author', '')
    author_list = authors.split(', ') if authors else []
    authors_formatted = ', '.join(author_list)

    # Get title
    title = entry.get('title', '')

    # Initialize citation variable
    citation = ""

    # Handle different formats based on entry type
    if entry_type == 'article':  # Journal article
        journal = entry.get('journal', '')
        volume = entry.get('volume', '')
        number = entry.get('number', '')
        pages = entry.get('pages', '')
        year = entry.get('year', '')
        
        # Generate journal article citation
        citation = f"{authors_formatted}. {title}. {journal}. {volume}({number}): {pages}, {year}."

    elif entry_type == 'inproceedings':  # Conference paper
        booktitle = entry.get('booktitle', '')
        year = entry.get('year', '')
        pages = entry.get('pages', '')
        
        # Generate conference paper citation
        citation = f"{authors_formatted}. {title}. In *{booktitle}*, pp. {pages}, {year}."
    
    elif entry_type == 'book':  # Book
        publisher = entry.get('publisher', '')
        year = entry.get('year', '')
        
        # Generate book citation
        citation = f"{authors_formatted}. {title}. {publisher}, {year}."
    
    elif entry_type == 'misc':  # Miscellaneous type
        year = entry.get('year', '')
        eprint = entry.get('eprint', '')
        archivePrefix = entry.get('archivePrefix', '')
        
        # Generate miscellaneous citation
        citation = f"{authors_formatted}. {title}. {archivePrefix}:{eprint}, {year}."

    # Handle missing fields and remove extra punctuation
    citation = citation.replace('..', '.').replace(' ,', ',').replace('()', '').replace('pp. ,', '')

    return citation

class BibTeXFetcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BibPaper")
        self.root.iconbitmap('logo.ico')    # logo
        self.root.geometry("600x400")
        # Initialize ttkbootstrap style
        self.style = Style(theme='litera')
        # Create GUI components
        self.create_widgets()
        # Create a queue for inter-thread communication
        self.result_queue = queue.Queue()

    def create_widgets(self):
        # Query label and input box
        self.query_label = tk.Label(self.root, text="Enter Paper Title:", font=("Arial", 10, "bold"))
        self.query_label.pack(pady=5)

        self.query_input = tk.Entry(self.root, width=50)
        self.query_input.pack(pady=5)

        # Fetch button
        self.fetch_button = tk.Button(self.root, text="Fetch BibTeX", font=("Arial", 10), command=self.on_fetch)
        self.fetch_button.pack(pady=10)
        
        # Create a frame to hold the result label and Cite button
        result_frame = tk.Frame(self.root)
        result_frame.pack(pady=5, fill="x", padx=10)
        
        # Result label
        self.result_label = tk.Label(result_frame, text="BibTeX Result:", font=("Arial", 10, "bold"))
        self.result_label.pack(side="left", padx=(30, 40))

        # Cite button
        self.cite_button = tk.Button(result_frame, text="Copy", font=("Times New Roman", 10), command=self.copy_to_clipboard) 
        self.cite_button.pack(side="right", padx=(10,50))  # Adjust button distance from the right
        
        # Scrolled text box for displaying results
        self.result_text = scrolledtext.ScrolledText(self.root, width=70, height=15, font=("Arial", 10))
        self.result_text.pack(pady=5)

    def on_fetch(self):
        query_string = self.query_input.get().strip()
        if not query_string:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "Please enter a valid query.")
            return

        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Fetching BibTeX...\n")

        # Create and start a thread to handle the search
        fetch_thread = threading.Thread(target=self.fetch_bibtex_thread, args=(query_string,))
        fetch_thread.start()

        # Check every 100 ms if there is new data in the queue, update the interface
        self.root.after(100, self.check_result)

    def fetch_bibtex_thread(self, query_string):
        # Call fetch_bibtex to get results
        bibtex = self.fetch_bibtex(query_string)

        # Put the result in the queue
        self.result_queue.put(bibtex)

    def copy_to_clipboard(self):
        # Get the text from the scrolled text box and copy to clipboard
        bibtex_result = self.result_text.get(1.0, tk.END).strip()
        if bibtex_result:
            pyperclip.copy(bibtex_result)  # Copy result to clipboard
            # self.result_text.delete(1.0, tk.END)
            # self.result_text.insert(tk.END, "BibTeX copied to clipboard!")

    def check_result(self):
        try:
            # Check if there is a new result in the queue
            result = self.result_queue.get_nowait()
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result)
        except queue.Empty:
            # If no result, continue waiting
            self.root.after(100, self.check_result)


    def fetch_bibtex(self, query_string):
        step = 0
        num_trials = 0  # Retry count

        # Set request parameters
        query_params = {
            "q": query_string,
            "h": 1,  # Fetch only one paper
            "f": step * 1000,
            "format": "bib"
        }
        query_url = "https://dblp.org/search/publ/api"  # DBLP API
        # Send the request
        res = requests.get(query_url, params=query_params)
        time.sleep(1)  # Wait for 1 second
        if res.status_code != requests.codes.ok or "Too Many Requests" in res.text:
            return "Timeout! Sleeping for a while!"
        else:
            if res.text == "":
                url = paperUrl(query_string)
                bib = getBib(url)
                if bib:
                    return bib
                else:
                    try:
                        metadata_list = fetch_arxiv_metadata(query_string)
                        if not metadata_list:
                            return "can't find in arxiv"

                        for metadata in metadata_list:
                            # get arXiv ID
                            arxiv_id = metadata['arxiv_id']
                            numeric_id = re.match(r'(\d+\.\d+)', arxiv_id) 
                            if numeric_id:
                                numeric_arxiv_id = numeric_id.group(1)
                                # ultilize arXiv ID to get BibTeX
                                bibtex_data = fetch_bibtex_from_arxiv(numeric_arxiv_id)
                                return bibtex_data
                            else:
                                return "can't find in arxiv" 

                    except Exception as e:
                        print(f"error: {e}")
            else:
                # Check for "eprinttype = {arXiv}" and exclude it
                if "arXiv" in res.text:
                # Use regex to find 'eprint' field and avoid mis-matching with 'eprinttype'
                    match = re.search(r"eprint\s*=\s*\{([^}]+)\}", res.text)
                    if match:
                        eprint_value = match.group(1)
                        # Pass eprint_value to fetch_bibtex_from_arxiv function
                        bibtex_data = fetch_bibtex_from_arxiv(eprint_value)
                        return bibtex_data
                    else:
                        return "No eprint field found."
                else:
                    updated_bibtex = update_bibtex_entry(res.text)
                    return updated_bibtex 
        return "No BibTeX found for the given query."


if __name__ == '__main__':
    root = tk.Tk()
    app = BibTeXFetcherApp(root)
    root.mainloop()
