from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import pandas as pd
import asyncio

def scrape_post(post_page):
    header = post_page.inner_html(".td-post-header")
    body = post_page.inner_html(".td-post-content")

    header_soup = BeautifulSoup(header, 'html.parser')
    body_soup = BeautifulSoup(body, 'html.parser')

    titles = [title.get_text() for title in header_soup.find_all("h1", class_="entry-title")]
    tags = [tag.a.get_text() for tag in header_soup.find_all("li", class_="entry-category")]
    authors = [author.get_text() for author in header_soup.find_all("div", class_="td-post-author-name")]
    published_date = [date.get_text() for date in header_soup.find_all("time", class_="entry-date")]
    date_str = header_soup.find("time", class_="entry-date").get("datetime")
    official_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z").astimezone(timezone.utc)
    body = [body_soup.get_text(separator=' ').replace('\n', '').strip()]
    
    image_links = [img['src'] for img in body_soup.find_all('img', class_='entry-thumb')]



    return {
        "title": titles,
        "tags": tags,
        "author": authors,
        "published_date": published_date,
        "official_date": official_date,
        "posts": body,
        "featured_image":image_links
    }
def scrape_post_with_timeout(post_page, item_link,g_byte, timeout_seconds=500):
    try:
        post_page.goto(item_link, timeout= timeout_seconds * 1000)
        post_data = scrape_post(post_page)
        g_byte.append(post_data)
    except TimeoutError:  
        print(f"Timeout occurred while processing: {item_link}")
    except Exception as e:
        print(f"Error scraping post: {e}")
    finally:
        post_page.close()

def main():
    g_byte = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()

        base_url = "https://www.gadgetbytenepal.com/blog-news-list/page/{}/"
        page_number = 701
        last_page=800
        while True:
            url = base_url.format(page_number)
            page.goto(url)
            posts = page.query_selector_all('.td_module_10')

            current_datetime_utc = datetime.now(timezone.utc)
            for post in posts:
                item_details = post.query_selector('.item-details')
                anchor = item_details.query_selector('a')
                item_link = anchor.get_attribute('href')

                post_page = browser.new_page()

                scrape_post_with_timeout(post_page, item_link,g_byte, timeout_seconds=60)

            if not posts:
                break
            page_number += 1

        browser.close()

    df = pd.DataFrame(g_byte)

    # Save the DataFrame to a CSV file
    csv_filename = f"gadget_posts_{last_page}.csv"
    df.to_csv(csv_filename, index=False)

    print(f"CSV file '{csv_filename}' saved with {len(df)} rows.")

if __name__ == "__main__":
    main()