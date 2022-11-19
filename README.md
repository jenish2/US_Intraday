1
Strategy name: “Hunter 6”
1. First trial version for strategy test.
2. Based on trading view standard indicators (not must)
3. Working mode 1,5,15,30 Minutes candles (Parameter)
4. Trading stocks in parallel (Min 4 Max 8)
5. Brokers: “Interactive Brokers” or “TD Ameritrade” https://www.tdameritrade.com/ (switch by
user)
6. Regular trading hours (not pre or close market)
7. Always close position before market close (sell in market price) dot hold over night.
8. EMA 20 Line (the yellow on the picture#1) should be based on ETH (Extended Trading Hours)
market time curve.
CCI and EMA 20 (Example)

2
The Buy signal example:
Conditions:
1. If the stock price crosses the EMA 20 line - from below the EMA to above the EMA more than in
X % “Delta Range” (GUI Parameter) See Picture 1 ->>> buy condition1 is ready.
2. If the CCI value > Y (Y= its parameter) buy condition 2 is ready.
3. If Condition 1 and 2 is TRUE, Buy signal activated.


![image](https://user-images.githubusercontent.com/62216295/202846023-909c6d49-4799-454f-a405-c4123da2e0b8.png)

![image](https://user-images.githubusercontent.com/62216295/202846067-f0cedea0-8f52-4fa6-9546-8568d610dea4.png)

![image](https://user-images.githubusercontent.com/62216295/202846077-748ac445-e5a6-4721-83b9-d99f03c3cf56.png)

![image](https://user-images.githubusercontent.com/62216295/202846100-dcb08c7f-e000-453b-bd44-b70edf84ad1d.png)
