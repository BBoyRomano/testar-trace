# Checkout with valid card
ID: UC-CHECKOUT-1
Actor: Shopper

## Preconditions
- The shopper is on the checkout page

## Main Flow
1. The shopper enters a valid card number
2. The shopper confirms the purchase
3. The system shows an order confirmation

## Alternative Flow
1. The system shows a payment validation error

## Postconditions
- The order is stored successfully
