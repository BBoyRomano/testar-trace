## UC.12 — Cancellation of the exam date

**Context of Use**
Teacher cancels the exam date for his/her subject

**Scope**
UIS

**Level**
user goal

**Primary Actor**
teacher

**Stakeholders and Interests**
- teacher: intends to cancel the exam date of his/her subject

**Constraints**
1. Only a exam date without graded students can be canceled

**Preconditions**
1. Teacher is already logged in to the UIS
2. Teacher is on the page My Exam Dates

**Trigger**
Teacher clicks on the button X in the row of the exam date

**Main Success Scenario**
1. Teacher clicks on the button X in the row of the exam date in the subject's sub-table
2. UIS will remove the exam date from the teacher's list of terms for the selected subject
3. Message confirming a successful execution will appear

**Postconditions**
1. Teacher is still on the page My Exam Dates
2. UIS removes the exam date from the teacher's list of terms for the selected subject and changes the DB and its tables accordingly
3. Message confirming a successful execution appears
4. The exam date is removed from the list in the sub-table in the menu My Exam Dates
5. The exam date is removed from the list in the menu Set Evaluation
6. The exam date is removed from the list in the menu Evaluation Table
7. Student's View: for every student with the subject enrolled the teacher and the cancelled term have disappeared on the sub-table of the subject in the menu Other Exam Dates

**Alternative Flows**
- **1a. Table has no entries, i.e. the teacher does not teach any subject at the moment**
  - 1a-1. The UC.12 cannot proceed

- **1b. Subject has empty sub-table i.e. the teacher does teach this subject but no exam dates have not been announced yet**
  - 1b-1. The UC.12 cannot proceed

- **1c. Teacher intends to cancel the exam date that has at least one student attending it**
  - 1c-1. Modal JS window will appear claiming that there are students registered in this exam term
  - 1c-2. Teacher will click on the button Cancel/Zrušit

  Postconditions:
  1. The screen of the menu My Exam Dates is still on
  2. No data are overwritten or changed

- **1d. Teacher intends to cancel the exam date that has at least one student attending it**
  - 1d-1. A modal JS window will appear claiming that there are students registered in this exam term
  - 1d-2. Teacher will click on the button OK

  Postconditions:
  1. The main success scenario continues from the step 2 onwards

- **1e. Buttons X are disabled for every exam date that has at least one student attending and at least one student on this exam date was already graded**
  - 1e-1. The UC.12 cannot proceed

- **2a. Internal error occurs in the UIS/DB during the cancellation of the subject's exam date in the DB**

  Postconditions:
  1. Page My Exam Dates is still displayed
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

**Technology and Data Variations List**
N/A

**Related Information**
- All of the taught subjects are displayed in sub-tables together with their exam terms
- Teacher can cancel any exam date with students already registered on it if no student has been graded on this exam date yet. These students have their term automatically cancelled.


---
