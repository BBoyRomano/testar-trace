## UC.07 — Cancellation of registered exam date

**Context of Use**
Student unregisters his/her exam date for the selected subject

**Scope**
UIS

**Level**
user goal

**Primary Actor**
student

**Stakeholders and Interests**
- student: intends to unregister his/her exam date for the selected subject

**Constraints**
N/A

**Preconditions**
1. Student is already logged in to the UIS
2. Student is on the page My Exam Dates

**Trigger**
Student clicks the button Unregister in the selected subject's row with an assigned date for an examination

**Main Success Scenario**
1. Student clicks on the button Unregister in the selected subject's row with an assigned date for an examination
2. UIS will remove the date of examination from the student's list of date for the selected subject
3. Message confirming a successful execution will appear

**Postconditions**
1. UIS removes the date of examination from the student's list of exam dates for the selected subject and edits its DB and its tables accordingly
2. Student is still on the page My Exam Dates
3. Message confirming a successful execution appears
4. Subject is removed from the list in the table under the menu My Exam Dates
5. The removed date appears in the sub-table under the menu Other Exam Dates
6. Teacher's View: the student disappears from the teacher's list of students enrolled on the selected subject's exam from the table located on the menu My Exam Dates
7. Teacher's View: the student disappears from the teacher's list of the selected subject's evaluations from the table located on the menu Set Evaluation
8. Teacher's View: the student disappears from the teacher's list of the selected subject's evaluations from the table located on the menu Evaluation Table

**Alternative Flows**
- **1a. Table has no entries, i.e. student has not assigned any exam date for yet**
  - 1a-1. The UC.07 cannot proceed

- **2a. Internal error occurs in the UIS/DB during cancellation of the subject's exam date registration in the DB**

  Postconditions:
  1. Student is still on the page My exam dates
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

**Technology and Data Variations List**
N/A

**Related Information**
- Listed subjects have their specific exam date assigned


---
