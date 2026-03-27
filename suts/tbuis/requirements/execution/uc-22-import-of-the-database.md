# Import of the database
ID: UC.22
Actor: Unlogged user

## Preconditions
- No one is logged in to the UIS - the upper menu has the option Export/Import DB

## Main flow
1. Unlogged user clicks on the Export/Import DB item on the menu
2. Unlogged user clicks on the Browse (or its bilingual equivalent) option in the form Import data into DB)
3. Unlogged user chooses the desired XML or JSON file
4. Unlogged user clicks on the button Import
5. Message confirming a successful execution will appear

## Alternative flow
1. 1a. Unlogged user clicks on the button Import
2. Postcondition: User is still on the page Export/Import DB
3. Postcondition: Message claiming an unsuccessful execution appears
4. Postcondition: No data are overwritten or changed
5. 4a. The imported file does not have a correct format or content
6. Postcondition: User is still on the page Export/Import DB
7. Postcondition: Message claiming an unsuccessful execution appears
8. Postcondition: No data are overwritten or changed
9. 4b. Internal error occurs in the UIS/DB during the setting of the new DB content
10. Postcondition: User is still on the page Export/Import DB
11. Postcondition: Message claiming an unsuccessful execution appears
12. Postcondition: No data are overwritten or changed

## Postconditions
- User is still on the page Export/Import DB
- Message confirming a successful execution appears
