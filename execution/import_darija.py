import requests
from bs4 import BeautifulSoup
import json
import os
import time

def scrape_darija():
    base_url = "https://www.darijawords.com/en/dictionary/browse"
    letters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
    
    dict_path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "darija.json")
    if os.path.exists(dict_path):
        with open(dict_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    print(f"Current dictionary size: {len(data)}")

    for letter in letters: # Scraping all letters
        print(f"Scraping letter: {letter}")
        url = f"{base_url}/{letter}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Updated selectors from DOM inspection
                cards = soup.find_all('a', class_='group')
                
                for card in cards:
                    headword_elem = card.find('div', class_='font-bold')
                    meaning_elem = card.find('div', class_='text-muted-foreground')
                    
                    if headword_elem and meaning_elem:
                        word = headword_elem.get_text(strip=True).lower()
                        meaning = meaning_elem.get_text(strip=True)
                        
                        if word not in data:
                            data[word] = {
                                "meaning": meaning,
                                "type": "imported",
                                "usage": f"Used in a sentence: {word}" # Fallback
                            }
            time.sleep(1) # Be nice
        except Exception as e:
            print(f"Error scraping {letter}: {e}")

    with open(dict_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Updated dictionary size: {len(data)}")

if __name__ == "__main__":
    scrape_darija()
