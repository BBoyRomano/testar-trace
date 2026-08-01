## UC.16 — Enters or reenters (changes) the evaluation of the examination

**Context of Use**
Teacher enters an evaluation of an examination of the selected student or changes already entered evaluation

**Scope**
UIS

**Level**
user goal

**Primary Actor**
teacher

**Stakeholders and Interests**
- teacher: intends to enter the student's evaluation of the subject or change already entered evaluation

**Constraints**
N/A

**Preconditions**
1. Teacher is already logged in to the UIS
2. Teacher is on the page Evaluation Table

**Trigger**
Teacher enters values and entries to the entry form of the filter

**Main Success Scenario**
1. Teacher chooses a subject from the dropdown menu of entry form Filter
2. If teacher wants only to enter new evaluations, he/she will keep the checkbox Includes students with already set grade unchecked
3. If teacher wants to search or change already entered evaluations, he/she will check the checkbox Includes students with already set grade.
4. Teacher clicks on the button Filter
5. Teacher chooses the desired evaluation of the student for a specific exam date from the dropdown menu
6. Teacher clicks on the button Submit
7. UIS enters the student's examination result for the selected subject
8. Message confirming a successful execution will appear

**Postconditions**
1. UIS enters the subject's evaluation to the student and changes the DB and its tables accordingly
2. Teacher is still on the page Evaluation Table
3. Message confirming a successful execution appears
4. The subject and its exam dates remain visible in the table Evaluation table
5. If the checkbox Includes students with already set grade is checked, the student and his/her evaluation remain visible in the table
6. If the checkbox Includes students with already set grade is not checked, the student is removed from the table
7. If the student scored A-E (i.e. he/she passed), he/she is removed from the list in the menu My Subjects
8. If the student scored F (i.e. he/she did not pass), he/she remains on the list in the menu My Subjects
9. Student is removed from the list of examination participans in the menu My Exam Dates
10. Student is removed from the list of examination participans in the menu Set Evaluation
11. Student's View: regardless of the evaluation the subject disappears from the table in the menu My Exam Dates
12. Student's View: if the student scored A-E (i.e. he/she passed), the subject is removed from the table Enrolled Subjects in the menu My Subjects
13. Student's View: if the student scored A-E (i.e. he/she passed), the credits are added to the amount in the header of the table Completed Subjects in the menu My Subjects
14. Student's View: if the student scored A-E (i.e. he/she passed), the subject appears with the achieved score in the table Completed Subjects in the menu My Subjects
15. Student's View: if the student scored A-E (i.e. he/she passed), the subject disappears from the table in the menu Other Exam Dates
16. Student's View: if the student scored F (i.e. he/she did not pass), the subject remains in the table Enrolled Subjects in the menu My Subjects
17. Student's View: if the student scored F (i.e. he/she did not pass), the subject remains in the table in the menu Other Exam Dates

**Alternative Flows**
- **1a. Dropdown menu in the entry form Filter does not show any subject, i.e. Teacher does not teach any subject at the moment**
  - 1a-1. The UC.16 cannot proceed

- **5a. If there is no exam date for the selected subject and the table Evaluation Table displays: No exam dates for this subject**
  - 5a-1. The UC.16 cannot proceed

- **6a. If the evaluated student is the last student registered on this term and the checkbox Includes students with already set grade. is unchecked**

  Postconditions:
  1. Conditions 1-17 of the main postcondition list are now enforced
  2. Selected term in the table Evaluation table in the menu Evaluation table displays: No students on this exam date

**Technology and Data Variations List**
N/A

**Related Information**
- After selecting the item of the Evaluation table menu the entry form Filter has predefined entry Select subject in the dropdown menu, i.e. the subject must be always chosen from the dropdown menu
- If student has not been evaluated yet, the entry list Grade is predefined as –


---
