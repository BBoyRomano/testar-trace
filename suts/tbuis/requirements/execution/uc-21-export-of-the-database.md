# Export of the database
ID: UC.21
Actor: unlogged user

## Preconditions
- >No one is logged in to the UIS - the upper menu has the option Export/Import DB

## Main flow
1. Unlogged user clicks on the Export/Import DB item on the menu
2. Unlogged user chooses either a XML or a JSON file in the Export DB to file form
3. Unlogged user clicks on the button Export
4. Message of a web browser will appear with input for specifying the location of the file
5. Web browser will save the file with a predefined name (e.g. `2019-12-02_18-11_DB-export.xml`) to the desired directory

## Postconditions
- User is still on the page Export/Import DB
