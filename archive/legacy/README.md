# Legacy artifacts (superseded)

These notebooks, SQL scripts, Excel reports, and the XGBoost model JSON come from an earlier version of this project.

They scraped OpenRice **HTML restaurant pages** with BeautifulSoup CSS selectors and threads, then loaded data into **MySQL** (including hardcoded connection settings in notebook cells).

**They are kept only for historical reference.** The maintained scraper lives in `src/openrice_scraper/` and uses OpenRice public JSON APIs instead.

Do not treat notebook MySQL credentials or HTML selectors as current practice.
