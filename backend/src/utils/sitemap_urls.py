import requests
import xml.etree.ElementTree as ET

import requests
import xml.etree.ElementTree as ET

def url_exists(url, headers):
    """Check if the URL exists by making a HEAD request."""
    try:
        response = requests.head(url, headers=headers, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False

def fetch_sitemap_urls(root_url):
    sitemap_url = f"{root_url}/sitemap.xml"  # Assuming standard sitemap location
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(sitemap_url, headers=headers)
    if response.status_code == 200:
        # Parse the XML, registering the namespaces
        ET.register_namespace('', "http://www.sitemaps.org/schemas/sitemap/0.9")
        sitemap = ET.fromstring(response.content)
        # Specify the namespace in the findall method
        namespace = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [url.find('s:loc', namespace).text for url in sitemap.findall('.//s:url', namespace) if url_exists(url.find('s:loc', namespace).text, headers)]
        return urls
    elif response.status_code == 404:
        # Sitemap not found, return an empty list
        return [root_url]
    else:
        return f"Failed to fetch sitemap, status code: {response.status_code}"

# urls = ["https://www.llamaindex.ai"]

# for url in urls:
#     print(f"working on {url}")
#     sitemap_urls = fetch_sitemap_urls(url)
#     for sitemap_url in sitemap_urls:
#         print(sitemap_url)


