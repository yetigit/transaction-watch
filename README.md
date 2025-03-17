# Make sense of your bank account transactions data


## Summary
- Getting the detailed data
    - The case of the SEB bank institution
    - "Scrapping" the data and why
- Categorizing the data
    - Categorizing using established tools, databases, etc.
    - Categorizing using a LLM
- Analyzing the data
- Conclusion

## Getting the detailed data

### "Scrapping" the data and why

### The case of the SEB bank institution

There are about 4 ways to check your transaction data if you have a SEB (Skandinaviska Enskilda Banken) bank account.

- using the mobile app
- using a third party app (fintech)
- PSD2 and the SEB API
- using the browser platform

**Now let's adress the problem with each of these options.**

---

## The mobile app

### Getting a bank statement 

From the mobile app it is simply not possible to download a bank statement.
Which in our case would be keen as the mobile app data displays richer context for each transaction.
One important piece of information it gives us is the purchase point or merchant name of the transaction.
This is an important detail, because the browser platform (which you CAN download a bank account statement from)
does not provide this data for the regular user.

### SEB's categorization

The categorization feature in the SEB mobile app is not just poor, it's not functional. 
More specifically it does not work well for transactions made outside of Sweden.

- wrong categories are applied
- changing the category via the app recategorizes what the app deems to be **similar** transactions (it's not similar)
- even if the proper category is chosen, it does not tell you what is the transaction about, what your actual money went in.

---

## Fintech solutions

It's already questionable to take that path considering most fintech apps linking your bank account are US based (not ideal if your services are located in europe, in the EU).
_Betterment_, _venmo_, _Wise_, to name a few. and more importantly **PLAID**, a bank account API aggregator serving these apps.
Here are some reasons I had to give up on this option:

- these apps mainly operate on mobile 
- these apps have a subscription model
- there have been concerns about these apps and the service feeding them, owning a little too much of your data.
(https://youtu.be/36Zi0T8-RTA?feature=shared)
- bypassing these points above by dealing with **PLAID** directly proved to be a waste of time 

### The PLAID fiasco

**PLAID** will let you work with their API on **real** data as a developer.
However in my specific case, only the `payment initiation` product is covered for SEB.
What's interesting is that for proxies such as Revolut and Wise all products are available. 
Including the one we are interested in `transactions`. 
While I do have Revolut, it is not the source of my daily spending. Making **PLAID** useless here.

---

## SEB API and PSD2

### PSD2
The **Revised Payment Services Directive (PSD2)** is a European regulation that aims to enhance competition, security, and innovation in the payments industry. It requires banks to open their payment services to third-party providers (TPPs) via secure APIs, enabling **Open Banking**. It strengthens consumer rights, mandates **strong customer authentication (SCA)** for online transactions, and reduces fraud risks. Enforced since 2018, PSD2 fosters transparency, encourages fintech growth, and improves the efficiency of digital payments across the EU.

### PSD2 `transactions` product

the SEB `transactions` API is simple. As a developer you can make a OAuth app and work in a **Sandbox** environment.
In pratice however, you _CANNOT_ work on **real** data. Why ? Because of security concerns. 
In order to access **real** data you need to be a company, with a **certificate** and implement rigorous protocols in your codebase.
Access to real data is basically only the luxury of startups and corporations, not of some individual who happens to be a developer. So I had to give up on using the SEB API.

---

## Browser online platform

If you log in to your bank account from a browser you can export a bank statement in excel or csv or pdf. 
However the data presented in this statement is rather poor. you have a data, an amount, a currency, a balance, and some (not)descriptive text.
Let's say you make a purchase in _Budapest_, well the descriptive text will be `BUDAPEST 20/02/2025`. That's it, nothing.
And in our case we would at least want **the purchase point**. this detail would indicate if my purchase was likely a beer or cigarettes or food.

However, the data is on the page, it's just not exported in the statement. <u>This is an opportunity for scrapping.</u>

---

# Scrapping the data
