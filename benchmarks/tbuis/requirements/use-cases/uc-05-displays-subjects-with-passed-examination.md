## UC.05 — Displays subjects with passed examination

**Context of Use**
Summarized information about all subjects with successful examination and their evaluations

**Scope**
UIS

**Level**
subfunction

**Primary Actor**
student

**Stakeholders and Interests**

- student: intends to get the summarized information about completed subjects including the sum of all credits he/she achieved

**Constraints**

1. Activity is only available in the menu My Subjects

**Preconditions**

1. Student is already logged in to the UIS

**Trigger**
Student clicks on the option My Subjects of the menu.

**Main Success Scenario**

1. Student clicks on the option My Subjects of the menu

**Postconditions**

1. Table Completed Subjects is displayed with a sum of achieved credits and a list of completed subjects with evaluation of all exam terms
2. No data are overwritten or changed

**Alternative Flows**

- **1a. Student has not completed any subject yet**

  Postconditions:
  1. Header of the table displays: 0 Total Credits
  2. Message No records appears in the table

**Technology and Data Variations List**
N/A

**Related Information**

- Completed subjects are listed alphabetically

---
