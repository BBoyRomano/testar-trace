## UC.03 — Change of user's personal data

**Context of Use**
Logged in user can change his/her first name and/or last name and/or email

**Scope**
UIS

**Level**
user goal

**Primary Actor**
Logged in user

**Stakeholders and Interests**
- student: intends to change his/her personal data
- teacher: intends to change his/her personal data

**Constraints**
1. First name must have at least 2 and not more than 30 characters
2. Last name must have at least 2 and not more than 30 characters
3. Email must have at least 8 and not more than 40 characters

**Preconditions**
1. User is already logged in to the UIS
2. User is located on the Overview page

**Trigger**
User edits one of his/her entries or the combination of them

**Main Success Scenario**
1. User will change data in the First name entry
2. User will change data in the Last name entry
3. User will change data in the Email entry
4. User will press the Update button

**Postconditions**
1. UIS saves changes and changes entries in the DB
2. User is still on the Overview page
3. Message confirming successful execution appears
4. If the user changed his/her first and/or last name, changes appear on the upper bar

**Alternative Flows**
- **1a. Entered first name has less than 2 characters**

  Postconditions:
  1. User is still on the Overview page
  2. Message notifying an unsuccessful execution appears
  3. No data are overwritten or changed

- **1b. Entered first name has more than 30 characters**

  Postconditions:
  1. User is still on the Overview page
  2. Message notifying an unsuccessful execution appears
  3. No data are overwritten or changed

- **2a. Entered last name has less than 2 characters**

  Postconditions:
  1. User is still on the Overview page
  2. Message notifying an unsuccessful execution appears
  3. No data are overwritten or changed

- **2b. Entered last name has more than 30 characters**

  Postconditions:
  1. User is still on the Overview page
  2. Message notifying an unsuccessful execution appears
  3. No data are overwritten or changed

- **3a. Entered email has less than 8 characters**

  Postconditions:
  1. User is still on the Overview page
  2. Message notifying an unsuccessful execution appears
  3. No data are overwritten or changed

- **3b. Entered email has more than 40 characters**

  Postconditions:
  1. User is still on the Overview page
  2. Message notifying an unsuccessful execution appears
  3. No data are overwritten or changed

**Technology and Data Variations List**
N/A

**Related Information**
- Overview page is visually and functionally identical for both the student and the teacher


---
