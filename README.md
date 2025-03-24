# TFT Discord Bot

This repository shows the modules and python files that work together to make my tft discord bot!. 
This bot has three main functions:
###   Retrieve and send the most recent tft patch notes
###   Retrieve and send requested tft patch notes
###   Automatically Update all discord servers that have granted permission with the newest tft patch notes 

main.py: The main module handles creating a discord client. From there it waits for users to use commands such as &tftrecent in their discord servers. This will then send discord embedded messages of tft patch notes directly to their server. It recieves data from the tft_data_retriever module and then formats embed messages to send to these servers.

tft_data_retriever.py: This module handles requests and html parsing of the tft patch notes web pages. This module then returns a list of HTML Data Tuples so that the main.py module can process them and format discord embed messages

guild_db_handler.py: This uses sqlite3 to store discord server ids and their permissions for the &starttftcheck command. I decided to give users the option to enable if they want their server to recieve tft updates or not when new patches release. 

## Examples of TFT Patch notes sent with Discord Embeds:
![tft-bot-examples\tftbotexample1.png]
![tft-bot-examples\tftbotexample2.png]