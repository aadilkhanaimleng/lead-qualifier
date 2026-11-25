import asyncio
from crawl4ai import AsyncWebCrawler

async def scrape_url(url: str) -> str:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        if not result.success:
            raise RuntimeError(f"Failed to scrape {url}: {result.error_message}")
        return result.markdown

if __name__ == "__main__":
    test_url = "https://example.com"
    markdown_text = asyncio.run(scrape_url(test_url))
    print("--- SCRAPED MARKDOWN ---")
    print(markdown_text[:1000])
