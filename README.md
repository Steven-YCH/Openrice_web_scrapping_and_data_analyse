# Openrice_web_scrapping_and_data_analyse

Scrape Hong Kong Restaurant from Openrice website, ETL with MySQL database stored procedure & provide analyse

1. Data Extraction
- Using Requests & Beautiful soup for webscraping to capture some HK reataurants information in Openrice.
- Using Threading to speed up the webscrapping process
- Provide base data cleansing and store data in MySQL database


2. Data Processing - MySQL stored procedure
- Perform ETL in MySQL database to transform data format
- Manage 1 to many relationship on restaurant to cusiine & dish by creating mapping table
