## UC.17 — Signs up to teach a subject

**Context of Use**
Teacher begins to teach a certain subject

**Scope**
UIS

**Level**
user goal

**Primary Actor**
teacher

**Stakeholders and Interests**
- teacher: intends to teach a subject

**Constraints**
1. One subject can be taught by up to 2 teachers

**Preconditions**
1. Teacher is already logged in to the UIS
2. Teacher is on the page Others' Subjects

**Trigger**
Teacher clicks on the button Participate in the row of the desired subject

**Main Success Scenario**
1. Teacher clicks on the button Participate in the row of the desired subject
2. UIS will add the subject to the teacher's list of subjects
3. Message confirming a successful execution will appear

**Postconditions**
1. UIS adds the subject to the teacher's list of subjects and changes the DB and its tables accordingly
2. Teacher is still on the page Others' Subjects
3. Message confirming a successful execution appears
4. The subject disappears from the list in the menu Others' Subjects
5. The subject appears in the table in the menu My Exam Dates and its' sub-table is empty (i.e. is without exam date)
6. The subject appears on the list in the menu New Exam Dates
7. The subject appears on the list in the menu Evaluation Table
8. The subject appears under this teacher on the list in the menu List of All Teachers
9. Student's View: to every student the teacher appears on the list of teachers leading the subject's sessions in the menu Other Subjects

**Alternative Flows**
- **1a. Table has no entries, i.e. the teacher already leads sessions (or is taking a part in the sessions) of all existing subjects**
  - 1a-1. The UC.17 cannot proceed

- **1b. Teacher intends to teach subject that is already taught by two other teachers**
  - 1b-1. The UC.17 cannot proceed

- **2a. Internal error occurs in the UIS/DB during the uploading of the information in the DB**

  Postconditions:
  1. Teacher is still on the page Others' Subjects
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

**Technology and Data Variations List**
N/A

**Related Information**
- All of the subjects that the teacher does not teach are displayed


---
