## UC.10 — Cancellation of registered subject

**Context of Use**
Teacher cancels a subject he/she teaches.

**Scope**
UIS

**Level**
user goal

**Primary Actor**
teacher

**Stakeholders and Interests**
- teacher: intends to cancel a subject he/she teaches

**Constraints**
1. Only a subject without enrolled students can be canceled

**Preconditions**
1. Teacher is already logged in to the UIS
2. Teacher is on the page My Subjects

**Trigger**
Teacher clicks on the button Remove located in the row of the subject intended for cancellation

**Main Success Scenario**
1. Teacher clicks on the button Remove located in the row of the subject intended for cancellation
2. UIS will remove the subject from the teacher's subject list
3. Message confirming a successful execution will appear

**Postconditions**
1. UIS removes the subject from the teacher's list of subjects and changes the DB and its tables accordingly
2. Teacher is still on the page My Subjects
3. Message confirming a successful execution appears
4. The subject is removed from the list in the menu My Subjects
5. The subject is removed from the list in the menu My Exam Dates
6. The subject is removed from the list in the menu New Exam Dates
7. The subject is removed from the list in the menu Set Evaluation
8. The subject is removed from the list in the menu Evaluation Table
9. The subject appears on the list in the menu Others' Subjects
10. The subject is removed from the teachers' list of subjects in the menu List of All Teachers for the specific teacher
11. Student's View: students must not find the removing teacher's name for the subject in the menu Other Subjects
12. Student's View: students must not find the removing teacher's name on the list of examining teachers for the selected subject in the menu Other Exam Dates

**Alternative Flows**
- **1a. Table has no entries, i.e. the teacher in not teaching any subjects at the moment**
  - 1a-1. The UC.10 cannot proceed

- **1b. Buttons Remove are disabled for every subject that has at least one student enrolled**
  - 1b-1. The UC.10 cannot proceed

- **2a. Internal error occurs in the UIS/DB during the cancellation of the subject in the DB**

  Postconditions:
  1. Teacher remains on the page My Subjects
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

**Technology and Data Variations List**
1. Teacher clicks on the button New exam date for the selected subject and UC.13 will proceed

**Related Information**
- All subjects are announced
- One subject can be simultaneously taught by up to two teachers. One cancellation by one teacher will have no effect on the other's subject.
- All exam dates for the subject are also terminated without warning with the cancellation of the subject.
- It is possible to create a exam date by clicking the New Exam Date button - more on the matter in UC.13
- It is possible to view the list of students enrolled on the subject by clicking the Students button - more on the matter in UC.13


---
