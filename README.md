# CS50-Finance
By *Jonathan Ngien via Harvard's CS50*

## Website description
- A web app where users can create and access their personal accounts to manage their portfolio of stocks
- Allow users to check real current stock prices and portfolio values as well as buy and sell stock by quering IEX for stocks' prices

---
### My Implementations
1. Completed the implementation of `register` that allows a user to sign up for an account via a form.
2. Completed the implementation of `quote` that allows a user to look up a stock’s current price.
3. Completed the implementation of `buy` that enables a user to purchase stocks.
4. Completed the implementation of `index` that displays an HTML table summarising which stocks the user owns, the numbers of shares owned, the current price of each stock, and the total value of each holding (i.e., shares times price). Also displays the user’s current cash balance along with a grand total.
5. Completed the implementation of `sell` that enables a user to sell shares of a stock (that he or she owns).
6. Completed the implementation of `history` that displays a HTML table summarizing all of a user’s transactions.
7. Implemented 2 other functionalities to allow users to change their passwords `change_password`, and to add additional cash to their account `addcash`.

**Disclaimer**: All code outside of the above functions were provided by Harvard's CS50

---
### Configuring and Running
1) You would have to register for an API key in order to be able to query IEX's data by accessing IEX's [website](https://iexcloud.io/cloud-login#/register/)
2) Then execute `$ export API_KEY=value` in terminal
    - If you don't have access to an account, you can use this API key: `export API_KEY=pk_b63bf394ebab4c43b3108bbb8e7f0720` (expires 17 March 23)
4) Run the program using `flask run`
5) More detailed information on setting up the IEX's APK can be found at CS50's [website](https://www.markdownguide.org/cheat-sheet/)
