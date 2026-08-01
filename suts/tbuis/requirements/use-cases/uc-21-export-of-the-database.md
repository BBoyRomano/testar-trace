## UC.21 — Export of the database

**Context of Use**
Unlogged user saves the current content of the database as an external XML/JSON file

**Scope**
UIS

**Level**
subfunction

**Primary Actor**
unlogged user

**Stakeholders and Interests**
- logged off user: intends to export the current content of the database

**Constraints**
N/A

**Preconditions**
1. >No one is logged in to the UIS - the upper menu has the option Export/Import DB

**Trigger**
Unlogged user clicks on the Export/Import DB item on the menu

**Main Success Scenario**
1. Unlogged user clicks on the Export/Import DB item on the menu
2. Unlogged user chooses either a XML or a JSON file in the Export DB to file form
3. Unlogged user clicks on the button Export
4. Message of a web browser will appear with input for specifying the location of the file
5. Web browser will save the file with a predefined name (e.g. `2019-12-02_18-11_DB-export.xml`) to the desired directory

**Postconditions**
1. User is still on the page Export/Import DB

**Alternative Flows**
N/A

**Technology and Data Variations List**
N/A

**Related Information**
N/A


---
