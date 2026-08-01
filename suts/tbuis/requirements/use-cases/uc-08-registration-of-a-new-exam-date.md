## UC.08 — Registration of a new exam date

**Context of Use**
Student registers a new exam date for the selected subject

**Scope**
UIS

**Level**
user goal

**Primary Actor**
student

**Stakeholders and Interests**
- student: intends to register a new exam date

**Constraints**
1. Student can be registered only for an one exam date for each subject
2. Student can register next date only if he/she received an evaluation i.e. (Grade) F
3. Student can register exam date only if this exam date has free registration available
4. Student can register successively maximum of 3 exam dates for each subject

**Preconditions**
1. Student is already logged in to the UIS
2. Student is located on the page Other Exam Dates

**Trigger**
Student clicks on the button Register located in a sub-table for the selected subject with an assigned exam date

**Main Success Scenario**
1. Student will click on the button Register located in a sub-table for the selected subject with an assigned examination term
2. UIS will add the date of an examination to the student's list of dates for the selected subject
3. Message confirming a successful execution will appear

**Postconditions**
1. UIS adds the date of an examination to the student's list of dates for the selected subject and changes its tables in the DB accordingly
2. Student is still on the page Other Exam Dates
3. Message confirming a successful execution appears
4. Exam date is removed from the subject's sub-table under the menu Other Exam Dates
5. In case of multiple exam dates for a single subject, the selected choice has a yellow background colour
6. Exam date appears with the subject on the table under the menu My Exam Dates
7. Teacher's View: the student appears on the teacher's list of students enrolled on the selected subject's exam from the table located on the menu My Exam Dates
8. Teacher's View: the student appears on the teacher's list of the selected subject's evaluations from the table located on the menu Set Evaluation
9. Teacher's View: the student appears on the teacher's list of the selected subject's evaluations from the table located on the menu Evalutaion Table

**Alternative Flows**
- **1a. Table has no entries in it, i.e. the student is not enrolled on any subject**
  - 1a-1. The UC.08 cannot proceed

- **1b. Sub-tables for selected subjects have no entries, i.e. student already registered exam dates for all subjects**
  - 1b-1. The UC.08 cannot proceed

- **1c. Table has subjects in it, yet their sub-tables have no entries, i.e. teachers did not announce any dates yet**
  - 1c-1. The UC.08 cannot proceed

- **1d. Button Register is disabled and entire sub-table has a yellow background i.e. the student already registered for exam date and teacher announced dates of other examinations**
  - 1d-1. The UC.08 cannot proceed

- **1e. Button Register is disabled and the button Participants shows that this exam date has no free registration available**
  - 1e-1. The UC.08 cannot proceed

- **1f. Two teachers teach this subject and each of them can announce up to three exam dates. The student has been already graded F three times. Now the student tries to registrate to second teachers' exam date (eg. fourth student's attempt). Student clicks on button Register.**

  Postconditions:
  1. Student is still on the page Other Exam Dates
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

- **2a. Internal error occurs in the UIS/DB during the subject's exam date registration in the DB**

  Postconditions:
  1. Student is still on the page Other Exam Dates
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

**Technology and Data Variations List**
N/A

**Related Information**
- Exam dates (if the subject has an exam date) can be found in sub-tables of all announced subjects.


---
