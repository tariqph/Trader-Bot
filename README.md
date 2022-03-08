# Trader Bot

This project is a trader bot trading in banknifty options. 

It is dockerized application with multiple containers.
There are four separate containers running in this application with following:
<ol>
  <li>Trading Script</li>
  <li>Selenium WebDriver</li>
  <li>RabbitMQ message broker</li>
  <li>PostgreSQL database</li>
</ol>

The diagram below illustrates the services used in the containers.


![traderbot drawio (2)](https://user-images.githubusercontent.com/14332590/157277197-fcc9fbd6-f9d2-463b-8383-999af8b18f83.png)
