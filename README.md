# WaybackWebsift

Tool to scrape emails, phone numbers, and links from a given URL either passively from archived sources or actively by requesting the URL.

![Demo](waybackwebsift.gif)

This project is a rewrite of [WebSift by s-r-e-e-r-a-j](https://github.com/s-r-e-e-r-a-j/WebSift)  in Python.

## Features

- **Scraping Emails**: Extract emails from visible text as well as from `mailto:` links.
- **Scraping Phone Numbers**: Extract phone numbers found in visible text and from `tel:` links.
- **Scraping Links**: Extract HTTP and HTTPS links from the page.
- **Passive Recon**: Fetch content from archived sources using [Wayback Machine](https://web.archive.org/) or [archive.is](http://archive.today/).

## Requirements

The project requires Python 3 and the following packages:

- [requests](https://pypi.org/project/requests/)
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)
- [simple-term-menu](https://pypi.org/project/simple-term-menu/)
- [colorama](https://pypi.org/project/colorama/)

A [requirements.txt](requirements.txt) file is provided for easy installation.

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yetanotherf0rked/waybackwebsift.git
cd waybackwebsift
```

2. **Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the main script:
```bash
python waybackwebsift.py
```
Follow the interactive prompts to choose the URL, the archive source (if any), the data to scrape, and whether or not you want to save the results in a specified folder.

# Known Issues
- When requesting archive.today, we get a 302 with a timeout before getting the URL. This is not supported yet by the script.
- Links extracted when using archivers are suffixed by their archived URLs.

## License
MIT
