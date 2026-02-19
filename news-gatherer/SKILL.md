---
name: news-gatherer
description: Gathers news and articles from official news websites and media platforms. Scrapes headlines, summaries, and metadata from multiple news sources. Use when user wants to collect information from news sites, media platforms, or official websites for content aggregation and monitoring.
license: Apache-2.0
metadata:
  author: skill-creating
  version: "1.0"
---

# News Gatherer

## Overview

This skill collects news articles and information from official news websites and media platforms. It provides structured extraction of headlines, summaries, publication dates, and article URLs, making it easy to aggregate and monitor content from multiple sources.

## Core Capabilities

- **Web Scraping**: Extracts news articles from websites using browser automation
- **Content Parsing**: Parses headlines, article text, publication dates, and metadata
- **Multi-Source Support**: Works with various news websites and media platforms
- **Structured Output**: Returns JSON-formatted data with article details
- **Error Handling**: Gracefully handles website structure changes and access issues

## How It Works

### Step 1: Navigate to Target Website

Use browser automation to navigate to the news website or media platform. Wait for the page to fully load, including any dynamic content loaded via JavaScript.

### Step 2: Identify News Articles

Scan the page to identify news article elements using common patterns:
- Article titles (usually in `<h1>`, `<h2>`, or `<h3>` tags)
- Article links (anchor tags within article containers)
- Publication dates (datetime or time elements)
- Article summaries or excerpts (paragraph elements)

### Step 3: Extract Article Data

For each identified article:
- Extract the headline/title
- Extract the article URL
- Extract publication date if available
- Extract summary or first paragraph
- Extract author information if available
- Capture any tags or categories

### Step 4: Structure the Output

Format extracted data into a structured JSON object:
```json
{
  "source": "website-name",
  "articles": [
    {
      "title": "Article Headline",
      "url": "https://...",
      "date": "2026-02-19T...",
      "summary": "Article summary...",
      "author": "Author name (optional)",
      "tags": ["tag1", "tag2"]
    }
  ],
  "extracted_at": "2026-02-19T..."
}
```

### Step 5: Handle Pagination (Optional)

If the news source has multiple pages:
- Detect pagination elements (Next, Load More, etc.)
- Iterate through pages to collect articles
- Limit to reasonable number of articles (default: 20-50)
- Respect rate limits and avoid overwhelming the server

## Usage

### Basic Usage

Provide a news website URL or specify a news source:

**Example Request:**
```
Gather news from https://techcrunch.com
```

**Actions:**
1. Navigate to TechCrunch homepage
2. Extract top articles (titles, URLs, summaries, dates)
3. Return structured JSON output

### Advanced Usage

**Specify Article Limit:**
```
Gather top 10 articles from https://reuters.com
```

**Filter by Topic:**
```
Find articles about AI from https://theverge.com
```

**Multiple Sources:**
```
Gather news from BBC, CNN, and Al Jazeera
```

**Extract Full Article Content:**
```
Get the full article content from https://example.com/article-123
```

## Examples

### Example 1: Gathering Tech News

**Input:**
```
Gather news from TechCrunch's AI section
```

**Actions:**
1. Navigate to `https://techcrunch.com/category/artificial-intelligence/`
2. Wait for page to load
3. Select all article cards in the main content area
4. Extract: title, URL, date, summary, author
5. Format as JSON

**Output:**
```json
{
  "source": "TechCrunch",
  "category": "Artificial Intelligence",
  "articles": [
    {
      "title": "OpenAI Launches New Model",
      "url": "https://techcrunch.com/2026/02/openai-new-model",
      "date": "2026-02-19T10:30:00Z",
      "summary": "OpenAI has announced...",
      "author": "Jane Smith"
    },
    {
      "title": "Google's AI Assistant Update",
      "url": "https://techcrunch.com/2026/02/google-ai-update",
      "date": "2026-02-19T09:15:00Z",
      "summary": "Google has updated...",
      "author": "John Doe"
    }
  ],
  "extracted_at": "2026-02-19T17:00:00Z",
  "article_count": 2
}
```

### Example 2: Monitoring Official News Site

**Input:**
```
Extract top 5 headlines from https://www.bbc.com/news
```

**Actions:**
1. Navigate to BBC News homepage
2. Find the main news section
3. Extract top 5 headline articles
4. Return only headlines and links

**Output:**
```json
{
  "source": "BBC News",
  "articles": [
    {
      "title": "Breaking: Major World Event",
      "url": "https://www.bbc.com/news/article-1"
    },
    {
      "title": "Another Important Story",
      "url": "https://www.bbc.com/news/article-2"
    }
  ],
  "extracted_at": "2026-02-19T17:00:00Z",
  "article_count": 5
}
```

## Edge Cases

### Paywall Content

**Issue**: Some news sites have paywalls that block article access.

**Handling**:
- Detect paywall indicators (subscription prompts, blurred content)
- Inform user that full content is behind paywall
- Provide available metadata (title, summary) that doesn't require paywall
- Suggest alternative sources if applicable

### Dynamic Content Loading

**Issue**: Articles load via JavaScript/AJAX after initial page load.

**Handling**:
- Wait for dynamic content to load before extracting
- Use scroll actions to trigger lazy-loading
- Monitor DOM changes and wait for stabilization
- Set reasonable timeout (e.g., 10-15 seconds)

### Website Structure Changes

**Issue**: News sites frequently update their HTML structure.

**Handling**:
- Use flexible selectors (multiple possible selectors for same element)
- Fallback to broader selectors if specific ones fail
- Log structure changes for future reference
- Recommend updating skill selectors periodically

### Anti-Bot Detection

**Issue**: Some sites detect and block automated scraping.

**Handling**:
- Use realistic user agent strings
- Add delays between requests (1-2 seconds)
- Respect robots.txt and rate limits
- Consider using authenticated APIs if available

### Empty Article Lists

**Issue**: No articles found on a news page.

**Handling**:
- Verify page loaded correctly
- Check for ad blockers or JavaScript errors
- Try alternative selectors
- Inform user if page structure doesn't match expectations
- Suggest manual verification of website

## Common Patterns

### News Site Structure Patterns

Most news sites follow these common patterns:

**Card-based Layout**:
- Articles in `<article class="card">` elements
- Grid or list of article cards
- Each card contains title, summary, date, link

**List-based Layout**:
- Articles in `<ul>` or `<ol>` lists
- Each `<li>` contains an article
- Titles are `<h2>` or `<h3>` within list items

**Section-based Layout**:
- Divided into categories/sections
- Each section has a headline section
- Articles follow section header

### Date Format Patterns

Common date formats to handle:
- ISO 8601: `2026-02-19T10:30:00Z`
- Relative: "2 hours ago", "Just now"
- Human-readable: "February 19, 2026"
- Short: "Feb 19, 2026"

### Title Hierarchy

Use semantic HTML to identify importance:
- `<h1>`: Main headline or page title
- `<h2>`: Section headers or top articles
- `<h3>`: Individual article titles in lists
- Use hierarchy to prioritize article selection

## Error Handling

### Navigation Failures

**Symptoms**: Cannot load or navigate to website

**Cause**: Network issues, website down, or blocked URL

**Solution**:
- Verify URL is correct and accessible
- Check network connectivity
- Try alternative URL (e.g., http vs https)
- Inform user of the specific error

### Extraction Failures

**Symptoms**: Page loads but no articles are extracted

**Cause**: Selector mismatch, JavaScript not loaded, or content blocked

**Solution**:
- Verify page loaded completely
- Try alternative selectors
- Check for dynamic content that needs triggering
- Examine page structure to identify correct selectors
- Fall back to simpler extraction methods

### Timeout Errors

**Symptoms**: Browser hangs or exceeds timeout

**Cause**: Slow page loads, infinite JavaScript loops, or network issues

**Solution**:
- Increase timeout value
- Reduce number of articles to extract
- Skip images or heavy resources
- Check for infinite scroll issues

### Rate Limiting

**Symptoms**: Website blocks requests after several attempts

**Cause**: Too many rapid requests trigger anti-bot measures

**Solution**:
- Add delays between requests
- Respect robots.txt guidelines
- Limit concurrent requests
- Use authenticated APIs when available

## Performance Notes

- **Page Load Time**: Allow 5-10 seconds for dynamic content
- **Extraction Time**: Typically 1-3 seconds per article
- **Batch Processing**: Limit to 20-50 articles per request for speed
- **Memory Usage**: Large pages may require pagination
- **Optimization**: Cache results for repeated queries

## Security Considerations

- **robots.txt**: Always check and respect robots.txt
- **Rate Limiting**: Implement delays to avoid overwhelming servers
- **User Privacy**: Don't collect user data or cookies
- **Content Verification**: Be cautious of potentially misleading or fake news
- **Terms of Service**: Ensure scraping complies with website ToS

## Requirements

- Browser automation tool (Playwright, Puppeteer, or equivalent MCP tool)
- JavaScript execution support for dynamic websites
- Wait and timeout handling capabilities
- DOM inspection and element selection
- JSON output formatting

## Troubleshooting

### No Articles Found

**Symptoms**: Page loads successfully but extraction returns 0 articles

**Cause**: Selector doesn't match current page structure

**Solution**:
1. Inspect the actual page HTML structure
2. Update selectors to match current structure
3. Test with sample elements
4. Consider using more generic selectors as fallback

### Page Structure Changed

**Symptoms**: Previously working selectors now fail

**Cause**: News website updated their HTML/CSS structure

**Solution**:
1. Check website for redesign updates
2. Inspect new page structure
3. Update selectors in skill
4. Add fallback selectors for robustness

### Content Behind Login

**Symptoms**: Only see headlines, full content requires authentication

**Cause**: Premium or subscriber-only content

**Solution**:
1. Inform user about paywall/login requirement
2. Extract available metadata (title, summary)
3. Suggest using official API if available
4. Consider alternative public sources

## References

- [Playwright Documentation](https://playwright.dev/docs/api/class-playwright)
- [Web Scraping Best Practices](https://docs.scrapy.org/en/latest/topics/practices.html)
- [robots.txt Checker](https://www.robotstxt.org/robotstxt.html)

## Version History

### v1.0.0
- Initial release
- Basic news extraction from websites
- Multi-source support
- JSON structured output
- Error handling for common edge cases
