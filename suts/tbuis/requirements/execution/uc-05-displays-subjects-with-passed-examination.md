# Displays subjects with passed examination
ID: UC.05
Actor: student

## Preconditions
- Student is already logged in to the UIS

## Main flow
1. Student clicks on the option My Subjects of the menu

## Alternative flow
1. 1a. Student has not completed any subject yet
2. Postcondition: Header of the table displays: 0 Total Credits
3. Postcondition: Message No records appears in the table

## Postconditions
- Table Completed Subjects is displayed with a sum of achieved credits and a list of completed subjects with evaluation of all exam terms
- No data are overwritten or changed
