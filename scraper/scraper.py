from seleniumwire import webdriver
from bs4 import BeautifulSoup
import csv
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

RANKINGS_URL = 'https://badmintonranks.com/ranking/bwf'

EVENT_TYPES = [
    'Men\'s Single',
    'Women\'s Single', 
    'Men\'s Double',
    'Women\'s Double',
    'Mixed Double'
]

class Scraper:
    def __init__(self):
        options = Options()
        # Set user agent to avoid detection
        options.set_preference("general.useragent.override", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0")
        
        self.driver = webdriver.Firefox(options=options)
        self.driver.implicitly_wait(15)
        self.driver.set_page_load_timeout(60)

    def scrape_event_type(self, event_type):
        """Scrape data for a specific event type"""
        print(f"\n🎯 Scraping {event_type}...")
        
        try:
            self.driver.get(RANKINGS_URL)
            
            print("Waiting for rankings to load...")

            # Wait for the dropdown to be clickable
            wait = WebDriverWait(self.driver, 15)
            
            # Find and click the Type dropdown input
            dropdown = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input.el-input__inner[placeholder='Type']"))
            )
            dropdown.click()
            time.sleep(1)  # Small delay for dropdown to open
            
            # Find and click the specific event option
            # The options appear in a dropdown list, we need to find the one with matching text
            all_options = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".el-select-dropdown__item"))
            )
            print(f"Found {len(all_options)} total elements with class el-select-dropdown__item")

            visible_options = [opt for opt in all_options if opt.is_displayed()]
            print(f"Found {len(visible_options)} VISIBLE dropdown options")
            
            # Print the text of visible options for debugging
            for i, opt in enumerate(visible_options):
                print(f"  Option {i}: '{opt.text}'")
            
            for option in visible_options:
                if event_type in option.text:
                    option.click()
                    print(f"✓ Selected {event_type}")
                    break

            time.sleep(0.5)
            search_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Search')] | //button[contains(@class, 'search')]"))
            )
            search_button.click()
            
            # Wait for table to reload with new data
            time.sleep(3)  # Give it time to load new data
            
            # Get the page source
            html_data = self.driver.page_source
            self.driver.quit()
            return html_data
            
        except Exception as e:
            print(f"Error selecting {event_type}: {e}")
            self.driver.quit()
            return None

    def extract_player_data(self, soup):
        """Extract player data from table cells"""
        players = []
        
        # Find all table cells
        cells = soup.find_all('td', class_='el-table__cell')
        
        # Group cells by 8 (8 columns per row)
        columns_per_row = 8
        
        for i in range(0, len(cells), columns_per_row):
            row_cells = cells[i:i+columns_per_row]
            
            if len(row_cells) < columns_per_row:
                continue
            
            try:
                # Extract rank (column 2)
                rank_cell = row_cells[1].find('div', class_='cell')
                rank = rank_cell.get_text(strip=True) if rank_cell else ''
                
                # Extract rank change (column 3)
                rank_diff_cell = row_cells[2].find('span', class_='rank-difference')
                rank_change = rank_diff_cell.get_text(strip=True) if rank_diff_cell else ''
                
                # Extract country (column 4)
                country_cell = row_cells[3].find('a', class_='link-type')
                country = country_cell.get_text(strip=True) if country_cell else ''
                
                # Extract player name (column 5)
                player_cell = row_cells[4].find('a', class_='link-type')
                if player_cell:
                    player_name = player_cell.find('span').get_text(strip=True) if player_cell.find('span') else ''
                else:
                    player_name = ''
                
                # Extract points (column 6)
                points_cell = row_cells[5].find('div', class_='cell')
                points = points_cell.get_text(strip=True) if points_cell else ''
                
                # Extract tournaments (column 7)
                tournaments_cell = row_cells[6].find('div', class_='cell')
                tournaments = tournaments_cell.get_text(strip=True) if tournaments_cell else ''
                
                # Extract last update (column 8)
                date_cell = row_cells[7].find('div', class_='cell')
                last_update = date_cell.get_text(strip=True) if date_cell else ''
                
                # Only add if we have at least a rank and player name
                if rank and player_name:
                    players.append({
                        'Rank': rank,
                        'Player Name': player_name,
                        'Country': country,
                        'Points': points,
                        'Tournaments': tournaments,
                        'Last Update': last_update,
                        'Rank Change': rank_change
                    })
            
            except Exception as e:
                print(f"Error parsing row: {e}")
                continue
        
        return players

    def save_to_csv(self, players, filename='badminton_rankings.csv'):
        """Save player data to CSV file"""
        if not players:
            print("No data to save!")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Rank', 'Player Name', 'Country', 'Points', 'Tournaments', 'Last Update', 'Rank Change']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for player in players:
                writer.writerow(player)
        
        print(f"✅ Saved {len(players)} players to {filename}")

if __name__ == '__main__':
    # Initialize the scraper and scrape the data
    scraper = Scraper()
    html_data = scraper.scrape_event_type('Men\'s Double')
    
    if html_data:
        # Parse HTML
        soup = BeautifulSoup(html_data, 'html.parser')
        
        # Extract player data
        players = scraper.extract_player_data(soup)
        
        # Display first few players
        print(f"\n📊 Found {len(players)} players")
        print("\nFirst 5 players:")
        for i, player in enumerate(players[:5], 1):
            print(f"{i}. {player['Rank']}. {player['Player Name']} ({player['Country']}) - {player['Points']} pts")
        
        # Save to CSV
        scraper.save_to_csv(players)
    else:
        print("Failed to scrape data")