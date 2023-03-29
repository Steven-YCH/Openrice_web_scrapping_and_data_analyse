# Openrice_web_scrapping_and_data_analyse

Scrape Hong Kong Restaurant from Openrice website, ETL with MySQL database stored procedure & provide analyse

1. Data Extraction
- Using Requests & Beautiful soup for webscraping to capture some HK reataurants information in Openrice.
- Using Threading to speed up the webscrapping process
- Provide base data cleansing and store data in MySQL database


2. Data Processing - MySQL stored procedure
- Perform ETL in MySQL database to transform data format using Stored Procedure
- Manage 1 to many relationship on restaurant to cusiine & dish by creating mapping table

3. Data Analyse - Hong Kong Restaurants Exploration
- Measuring Restaurants Popularity by Openrice Star number & Bookmark count to see what type of restaurant is most popular in HK using SQL

Sample of output
![image](https://user-images.githubusercontent.com/85422707/228155051-f5ed9bfe-74d5-47b6-8907-cc9b759b5272.png)


4. Predicting Popularity by ML
Using number of Bookmark as indicator of popularity, predicting by differenct features from openrice using XG Boost
