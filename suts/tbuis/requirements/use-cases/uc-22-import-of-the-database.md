## UC.22 — Import of the database

**Context of Use**
Unlogged user rewriters the current content of the database with the content of external XML or JSON file

**Scope**
UIS

**Level**
subfunction

**Primary Actor**
Unlogged user

**Stakeholders and Interests**
- logged off user: intends to set the content of the database to desired values

**Constraints**
N/A

**Preconditions**
1. No one is logged in to the UIS - the upper menu has the option Export/Import DB

**Trigger**
Unlogged user clicks on the Export/Import DB item on the menu

**Main Success Scenario**
1. Unlogged user clicks on the Export/Import DB item on the menu
2. Unlogged user clicks on the Browse (or its bilingual equivalent) option in the form Import data into DB)
3. Unlogged user chooses the desired XML or JSON file
4. Unlogged user clicks on the button Import
5. Message confirming a successful execution will appear

**Postconditions**
1. User is still on the page Export/Import DB
2. Message confirming a successful execution appears

**Alternative Flows**
- **1a. Unlogged user clicks on the button Import**

  Postconditions:
  1. User is still on the page Export/Import DB
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

- **4a. The imported file does not have a correct format or content**

  Postconditions:
  1. User is still on the page Export/Import DB
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

- **4b. Internal error occurs in the UIS/DB during the setting of the new DB content**

  Postconditions:
  1. User is still on the page Export/Import DB
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

**Technology and Data Variations List**
N/A

**Related Information**
N/A
