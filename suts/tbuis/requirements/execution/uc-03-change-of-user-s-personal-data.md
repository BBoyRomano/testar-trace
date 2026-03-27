# Change of user's personal data
ID: UC.03
Actor: Logged in user

## Preconditions
- User is already logged in to the UIS
- User is located on the Overview page

## Main flow
1. User will change data in the First name entry
2. User will change data in the Last name entry
3. User will change data in the Email entry
4. User will press the Update button

## Alternative flow
1. 1a. Entered first name has less than 2 characters
2. Postcondition: User is still on the Overview page
3. Postcondition: Message notifying an unsuccessful execution appears
4. Postcondition: No data are overwritten or changed
5. 1b. Entered first name has more than 30 characters
6. Postcondition: User is still on the Overview page
7. Postcondition: Message notifying an unsuccessful execution appears
8. Postcondition: No data are overwritten or changed
9. 2a. Entered last name has less than 2 characters
10. Postcondition: User is still on the Overview page
11. Postcondition: Message notifying an unsuccessful execution appears
12. Postcondition: No data are overwritten or changed
13. 2b. Entered last name has more than 30 characters
14. Postcondition: User is still on the Overview page
15. Postcondition: Message notifying an unsuccessful execution appears
16. Postcondition: No data are overwritten or changed
17. 3a. Entered email has less than 8 characters
18. Postcondition: User is still on the Overview page
19. Postcondition: Message notifying an unsuccessful execution appears
20. Postcondition: No data are overwritten or changed
21. 3b. Entered email has more than 40 characters
22. Postcondition: User is still on the Overview page
23. Postcondition: Message notifying an unsuccessful execution appears
24. Postcondition: No data are overwritten or changed

## Postconditions
- UIS saves changes and changes entries in the DB
- User is still on the Overview page
- Message confirming successful execution appears
- If the user changed his/her first and/or last name, changes appear on the upper bar
