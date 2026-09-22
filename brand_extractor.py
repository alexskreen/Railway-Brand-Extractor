import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
import os
import re
from pathlib import Path
from PIL import Image
from io import BytesIO
from typing import Optional, Dict, List, Tuple


class BrandExtractor:
    def __init__(self, url: str, output_dir: str = "./brand_assets"):
        """
        Initialize the BrandExtractor with a URL.

        Args:
            url: The website URL to analyze
            output_dir: Directory to save downloaded assets
        """
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        self.url = url
        self.output_dir = output_dir
        self.domain = urlparse(url).netloc.replace('www.', '')
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        self.driver = None
        self.page_html = None
        self.soup = None
        self.result = {
            'url': url,
            'domain': self.domain,
            'logo': None,
            'logo_url': None,
            'background_image': None,
            'background_image_url': None,
            'background_colors': [],
            'primary_font_color': None,
            'secondary_font_color': None,
            'button_color': None,
            'errors': []
        }

    def _init_driver(self):
        """Initialize Selenium WebDriver with webdriver-manager."""
        if self.driver is None:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")

            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                self.result['errors'].append(f"Failed to initialize Chrome driver: {str(e)}")
                raise

    def _close_driver(self):
        """Close Selenium WebDriver."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except Exception:
            pass

    def _fetch_page(self) -> bool:
        """Fetch the page using Selenium."""
        try:
            self._init_driver()
            self.driver.set_page_load_timeout(15)
            self.driver.get(self.url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
            )
            self.page_html = self.driver.page_source
            self.soup = BeautifulSoup(self.page_html, 'html.parser')
            return True
        except Exception as e:
            self.result['errors'].append(f"Failed to fetch page: {str(e)}")
            return False

    def _hex_to_rgb(self, hex_color: str) -> Optional[Tuple[int, int, int]]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.strip().lstrip('#')
        try:
            if len(hex_color) == 6:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            elif len(hex_color) == 3:
                return tuple(int(hex_color[i]*2, 16) for i in range(3))
        except ValueError:
            return None
        return None

    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color."""
        return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

    def _parse_color(self, color_str: str) -> Optional[str]:
        """Parse various color formats and return hex."""
        if not color_str:
            return None

        color_str = color_str.strip().lower()

        if color_str.startswith('#'):
            rgb = self._hex_to_rgb(color_str)
            return color_str if rgb else None

        rgb_match = re.match(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', color_str)
        if rgb_match:
            r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
            return self._rgb_to_hex((r, g, b))

        named_colors = {
            'white': '#ffffff', 'black': '#000000', 'red': '#ff0000',
            'green': '#008000', 'blue': '#0000ff', 'gray': '#808080',
            'grey': '#808080', 'transparent': None
        }

        return named_colors.get(color_str)

    def _find_logo(self) -> bool:
        """Find and download the logo."""
        logo_urls = []

        logo_selectors = [
            ('img[src*="logo"]', 'src'),
            ('img[alt*="logo" i]', 'src'),
            ('img.logo', 'src'),
            ('img#logo', 'src'),
            ('img[id*="logo"]', 'src'),
            ('a.logo img', 'src'),
            ('a#logo img', 'src'),
            ('[class*="logo"] img', 'src'),
            ('[id*="logo"] img', 'src'),
            ('img[class*="brand"]', 'src'),
            ('img.brand', 'src'),
        ]

        for selector, attr in logo_selectors:
            try:
                elements = self.soup.select(selector)
                for elem in elements:
                    url = elem.get(attr)
                    if url and url not in logo_urls:
                        logo_urls.append(urljoin(self.url, url))
                        if len(logo_urls) >= 3:
                            break
            except Exception:
                pass

        if logo_urls:
            for logo_url in logo_urls:
                if self._download_logo(logo_url):
                    return True

            if logo_urls:
                self.result['logo_url'] = logo_urls[0]
                return True

        return False

    def _download_logo(self, logo_url: str) -> bool:
        """Download and save the logo."""
        try:
            response = requests.get(logo_url, timeout=10)
            response.raise_for_status()

            if not response.content:
                return False

            try:
                img = Image.open(BytesIO(response.content))

                if img.format and img.format != 'PNG':
                    img = img.convert('RGBA')
                elif not img.format:
                    img = img.convert('RGBA')

                logo_path = os.path.join(self.output_dir, f"{self.domain}_logo.png")
                img.save(logo_path, 'PNG')

                self.result['logo'] = logo_path
                self.result['logo_url'] = logo_url
                return True
            except Exception:
                self.result['logo_url'] = logo_url
                return False

        except Exception:
            return False

    def _find_background_image(self) -> bool:
        """Find and download background image."""
        bg_image_urls = []

        elements_to_check = [
            self.soup.find('body'),
            self.soup.find('main'),
            self.soup.find('header'),
            self.soup.find('section'),
        ]

        for elem in elements_to_check:
            if not elem:
                continue

            style = elem.get('style', '')
            bg_match = re.search(r'background(?:-image)?:\s*url\([\'"]?([^\)\'\"]+)[\'"]?\)', style)
            if bg_match:
                bg_url = bg_match.group(1)
                bg_image_urls.append(urljoin(self.url, bg_url))

        if bg_image_urls:
            for bg_url in bg_image_urls:
                if self._download_background_image(bg_url):
                    return True

        return False

    def _download_background_image(self, bg_url: str) -> bool:
        """Download and save background image."""
        try:
            response = requests.get(bg_url, timeout=10)
            response.raise_for_status()

            img = Image.open(BytesIO(response.content))

            bg_path = os.path.join(self.output_dir, f"{self.domain}_background.png")
            if img.format != 'PNG':
                img = img.convert('RGB')
            img.save(bg_path, 'PNG')

            self.result['background_image'] = bg_path
            self.result['background_image_url'] = bg_url
            return True
        except Exception as e:
            self.result['errors'].append(f"Failed to download background image: {str(e)}")
            return False

    def _extract_colors(self):
        """Extract colors using Selenium computed styles."""
        try:
            if not self.driver:
                return

            # Background color
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                bg_color = body.value_of_css_property("background-color")
                if bg_color and bg_color not in ['rgba(0, 0, 0, 0)', 'transparent']:
                    color = self._parse_color(bg_color)
                    if color and color not in self.result['background_colors']:
                        self.result['background_colors'].append(color)
            except Exception:
                pass

            # Button color
            try:
                button_selectors = ['button', '[class*="btn"]', '[class*="cta"]']
                for selector in button_selectors:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if buttons and not self.result['button_color']:
                        button = buttons[0]
                        bg_color = button.value_of_css_property("background-color")
                        if bg_color and bg_color not in ['rgba(0, 0, 0, 0)', 'transparent']:
                            color = self._parse_color(bg_color)
                            if color:
                                self.result['button_color'] = color
                                break
            except Exception:
                pass

            # Font colors
            font_colors = []
            try:
                for tag in ['h1', 'h2', 'p', 'a']:
                    elements = self.driver.find_elements(By.TAG_NAME, tag)
                    for elem in elements[:3]:
                        try:
                            color = elem.value_of_css_property("color")
                            if color:
                                hex_color = self._parse_color(color)
                                if hex_color and hex_color not in font_colors and hex_color not in ['#ffffff']:
                                    font_colors.append(hex_color)
                        except Exception:
                            pass

                    if len(font_colors) >= 2:
                        break
            except Exception:
                pass

            if font_colors:
                self.result['primary_font_color'] = font_colors[0]
                if len(font_colors) > 1:
                    self.result['secondary_font_color'] = font_colors[1]

        except Exception as e:
            self.result['errors'].append(f"Error extracting colors: {str(e)}")

    def extract(self) -> Dict:
        """Main method to extract all brand information."""
        try:
            if not self._fetch_page():
                return self.result

            self._find_logo()
            self._find_background_image()
            self._extract_colors()

            if not self.result['background_colors']:
                self.result['background_colors'] = ['#ffffff']

            return self.result

        finally:
            self._close_driver()


def extract_brand(url: str, output_dir: str = "./brand_assets") -> Dict:
    """Convenience function to extract brand information from a URL."""
    extractor = BrandExtractor(url, output_dir)
    return extractor.extract()


if __name__ == "__main__":
    import json

    test_url = "https://www.github.com"
    result = extract_brand(test_url)

    print(json.dumps({k: v for k, v in result.items() if k != 'errors'}, indent=2))
    if result['errors']:
        print("\nErrors encountered:")
        for error in result['errors']:
            print(f"  - {error}")
