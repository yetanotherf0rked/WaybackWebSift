#!/usr/bin/env python3

import os
import sys
import re
import requests
from bs4 import BeautifulSoup
from simple_term_menu import TerminalMenu
from colorama import Fore, Style, init

init(autoreset=True)

# ---------------------------
# Color definitions with colorama
# ---------------------------
BrightGreen = Fore.GREEN + Style.BRIGHT
BrightRed = Fore.RED + Style.BRIGHT
BrightYellow = Fore.YELLOW + Style.BRIGHT
BrightWhite = Fore.WHITE + Style.BRIGHT
Cyan = Fore.CYAN + Style.BRIGHT
ResetColor = Style.RESET_ALL

# ---------------------------
# Helper functions for colored markers
# ---------------------------
def marker_info():
    """Returns the colorized [*] marker (informational)."""
    return f"{BrightWhite}[{Cyan}*{BrightWhite}]"

def marker_warning():
    """Returns the colorized [!] marker (warning/error)."""
    return f"{BrightWhite}[{BrightRed}!{BrightWhite}]"

def marker_success():
    """Returns the colorized [✓] marker (success)."""
    return f"{BrightWhite}[{BrightGreen}✓{BrightWhite}]"

# ------------------------------------------------------------------
# Banner (as requested)
# ------------------------------------------------------------------
def display_banner():
    # Optionally clear the screen: os.system('clear' if os.name == 'posix' else 'cls')
    print(f"""{BrightGreen}
    
    ▄   ▄ ▗▞▀▜▌▄   ▄ ▗▖▗▞▀▜▌▗▞▀▘█  ▄     ▄   ▄ ▗▞▀▚▖▗▖        ▄▄▄ ▄ ▗▞▀▀▘■  
    █ ▄ █ ▝▚▄▟▌█   █ ▐▌▝▚▄▟▌▝▚▄▖█▄▀      █ ▄ █ ▐▛▀▀▘▐▌       ▀▄▄  ▄ ▐▌▗▄▟▙▄▖
    █▄█▄█       ▀▀▀█ ▐▛▀▚▖      █ ▀▄     █▄█▄█ ▝▚▄▄▖▐▛▀▚▖    ▄▄▄▀ █ ▐▛▀▘▐▌  
               ▄   █ ▐▙▄▞▘      █  █                ▐▙▄▞▘         █ ▐▌  ▐▌  
                ▀▀▀                                                     ▐▌  
""")
    print(f"{Cyan}* Scraps emails, phone numbers and links from a URL")
    print(f"{BrightGreen}* Supports Passive Sources (WaybackMachine, archive.is) or the actual URL")
    print(f"{BrightYellow}* Rewrite of s-r-e-e-r-a-j/WebSift by yetanotherf0rked in Python\n")

# ------------------------------------------------------------------
# Check internet connection
# ------------------------------------------------------------------
def check_connection():
    print(f"{marker_info()} {Cyan}Checking internet connection...")
    try:
        requests.get("http://google.com", timeout=5)
        print(f"{marker_success()} {BrightGreen}Connected to the internet.")
    except requests.RequestException:
        print(f"{marker_warning()} {BrightRed}No internet connection detected. Try again later.")
        sys.exit(1)

# ------------------------------------------------------------------
# Validate URL
# ------------------------------------------------------------------
def is_valid_url(url):
    pattern = r'(https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]*[-A-Za-z0-9+&@#/%=~_|]'
    return re.match(pattern, url) is not None

# ------------------------------------------------------------------
# Wayback Machine check
# ------------------------------------------------------------------
def check_wayback_machine(url):
    """Return the archived WaybackMachine URL if available, else None."""
    try:
        api_url = "http://archive.org/wayback/available?url=" + url
        r = requests.get(api_url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            archived_snapshots = data.get("archived_snapshots")
            if archived_snapshots and "closest" in archived_snapshots:
                wayback_url = archived_snapshots["closest"].get("url")
                if wayback_url:
                    return wayback_url
    except Exception as e:
        pass
    return None

# ------------------------------------------------------------------
# archive.today / archive.is check
# ------------------------------------------------------------------
def check_archive_today(url):
    """Return an archive.today link if it redirects or indicates a snapshot exists, else None."""
    try:
        archive_url = "https://archive.today/?run=1&url=" + url
        r = requests.get(archive_url, timeout=5, allow_redirects=True)
        # If we get a final URL containing archive.today, archive.ph, or archive.is, assume it's archived.
        if r.status_code == 200 and any(x in r.url for x in ["archive.today", "archive.ph", "archive.is"]):
            return r.url
    except Exception as e:
        pass
    return None

# ------------------------------------------------------------------
# Fetch raw HTML (no cleaning yet)
# ------------------------------------------------------------------
def fetch_raw_content(url):
    try:
        response = requests.get(url, timeout=20)  # increased to 20
        if response.status_code == 200:
            return response.text
    except Exception as e:
        pass
    return ""

# ------------------------------------------------------------------
# Email scraping (includes mailto: attributes)
# ------------------------------------------------------------------
def scrape_emails_from_html(html):
    emails = set()

    soup = BeautifulSoup(html, "html.parser")
    # Remove unwanted tags
    for elem in soup(["script", "style", "noscript"]):
        elem.decompose()
    visible_text = soup.get_text(separator="\n")
    
    # Regex-based extraction from visible text
    email_pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
    found_in_text = set(re.findall(email_pattern, visible_text, flags=re.IGNORECASE))
    emails.update(found_in_text)
    
    # Extract emails from mailto: links
    for link in soup.find_all("a", href=True):
        href_val = link["href"]
        if href_val.startswith("mailto:"):
            possible_email = href_val.replace("mailto:", "").strip()
            emails.update(re.findall(email_pattern, possible_email, flags=re.IGNORECASE))
    
    return emails

# ------------------------------------------------------------------
# Phone scraping (visible text + href="tel:")
# ------------------------------------------------------------------
def scrape_phones_from_html(html):
    phones = set()

    soup = BeautifulSoup(html, "html.parser")
    for elem in soup(["script", "style", "noscript"]):
        elem.decompose()
    visible_text = soup.get_text(separator="\n")
    
    # Regex-based extraction of common phone number formats
    phone_pattern = r'(\d{3}-\d{3}-\d{4})|(\(\d{3}\)\d{3}-\d{4})|(\b\d{10}\b)|(\d{3}\s\d{3}\s\d{4})'
    matches = re.findall(phone_pattern, visible_text)
    for match_tuple in matches:
        for group in match_tuple:
            if group:
                phones.add(group.strip())
    
    # Extract phone numbers from tel: links
    for link in soup.find_all("a", href=True):
        href_val = link["href"]
        if href_val.startswith("tel:"):
            phone_raw = href_val.replace("tel:", "").strip()
            phones.add(phone_raw)
    
    return phones

# ------------------------------------------------------------------
# Social link scraping (do not alter links)
# ------------------------------------------------------------------
def scrape_social_links(html, from_wayback=False, from_archiveis=False):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    
    # Get all <a href=""> links that begin with http:// or https://
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http://") or href.startswith("https://"):
            links.add(href)
    return links

# ------------------------------------------------------------------
# Save data
# ------------------------------------------------------------------
def save_to_folder(emails, phones, socials):
    folder_name = input(f"{marker_info()} {Cyan}Enter folder name : {BrightWhite}")
    if os.path.isdir(folder_name):
        print(f"{marker_warning()} {BrightRed}Folder already exists.")
        return save_to_folder(emails, phones, socials)
    os.mkdir(folder_name)

    if emails:
        with open(os.path.join(folder_name, "email_output.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(emails)))
    if phones:
        with open(os.path.join(folder_name, "phone_output.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(phones)))
    if socials:
        with open(os.path.join(folder_name, "social_media_output.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(socials)))
    
    print(f"{marker_success()} {BrightGreen}Output saved successfully in {folder_name}")

# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
def main():
    display_banner()
    check_connection()

    target_url = input(f"{marker_info()} {Cyan}Enter URL: {BrightWhite}")
    while not is_valid_url(target_url):
        print(f"{marker_warning()} {BrightRed}Invalid URL. Please try again.")
        target_url = input(f"{marker_info()} {Cyan}Enter URL: {BrightWhite}")
    
    # Check passive sources
    wayback_link = check_wayback_machine(target_url)
    archive_today_link = check_archive_today(target_url)
    
    # Build dynamic menu for source selection
    print(f"{marker_info()} {Cyan}Choose how to fetch the page")
    menu_items = []
    if wayback_link:
        menu_items.append(f"WaybackMachine Latest Snapshot: {wayback_link}")
    if archive_today_link:
        menu_items.append(f"archive.today Latest Snapshot: {archive_today_link}")
    menu_items.append(f"Fetch the actual URL: {target_url}")
    terminal_menu = TerminalMenu(menu_items)
    choice_index = terminal_menu.show()
    
    if choice_index is None:
        print(f"{marker_warning()} {BrightRed}No valid choice selected. Exiting...")
        sys.exit(0)
    
    chosen_item = menu_items[choice_index]
    chosen_url = None
    from_wayback = False
    from_archiveis = False
    
    if chosen_item.startswith("WaybackMachine"):
        chosen_url = wayback_link
        from_wayback = True
    elif chosen_item.startswith("archive.today"):
        chosen_url = archive_today_link
        from_archiveis = True
    else:
        chosen_url = target_url

    # Prompt the user for which data to scrape
    email_option = input(f"{marker_info()} {Cyan}Scrape emails from website? (y/n) : {BrightWhite}")
    phone_option = input(f"{marker_info()} {Cyan}Scrape phone numbers from website? (y/n) : {BrightWhite}")
    social_option = input(f"{marker_info()} {Cyan}Scrape social media/other links from website? (y/n) : {BrightWhite}")
    
    if (email_option.lower() not in ["y", "yes"] and
        phone_option.lower() not in ["y", "yes"] and
        social_option.lower() not in ["y", "yes"]):
        print(f"{marker_warning()} {BrightRed}No scraping option selected. Exiting...")
        sys.exit(0)
    
    print(f"{marker_info()} {Cyan}Scraping started")
    
    raw_html = fetch_raw_content(chosen_url)
    if not raw_html:
        print(f"{marker_warning()} {BrightRed}Failed to fetch content. Exiting...")
        sys.exit(0)
    
    found_emails = set()
    found_phones = set()
    found_socials = set()
    
    if email_option.lower() in ["y", "yes"]:
        found_emails = scrape_emails_from_html(raw_html)
        if found_emails:
            print(f"{marker_success()} {BrightGreen}Emails extracted successfully:")
            for e in sorted(found_emails):
                print(e)
        else:
            print(f"{marker_warning()} {BrightRed}No emails found.")
    
    if phone_option.lower() in ["y", "yes"]:
        found_phones = scrape_phones_from_html(raw_html)
        if found_phones:
            print(f"{marker_success()} {BrightGreen}Phone numbers extracted successfully:")
            for p in sorted(found_phones):
                print(p)
        else:
            print(f"{marker_warning()} {BrightRed}No phone numbers found.")
    
    if social_option.lower() in ["y", "yes"]:
        found_socials = scrape_social_links(raw_html, from_wayback=from_wayback, from_archiveis=from_archiveis)
        if found_socials:
            print(f"{marker_success()} {BrightGreen}Social/other links extracted successfully:")
            for s in sorted(found_socials):
                print(s)
        else:
            print(f"{marker_warning()} {BrightRed}No social media links or other links were found.")
    
    if found_emails or found_phones or found_socials:
        save_option = input(f"{marker_info()} {Cyan}Do you want to save the output? (y/n) : {BrightWhite}")

        if save_option.lower() in ["y", "yes"]:
            save_to_folder(found_emails, found_phones, found_socials)
    
    print(f"{marker_warning()} {BrightRed}Exiting....\n")

if __name__ == "__main__":
    main()

