## UC.04 — Cancelling the registration (enrollment) to a subject

**Context of Use**
Student cancels the registration to a subject he/she previously enrolled

**Scope**
UIS

**Level**
user goal

**Primary Actor**
student

**Stakeholders and Interests**
- student: intends to cancel the registration to a subject

**Constraints**
N/A

**Preconditions**
1. Student is logged in to the UIS
2. User is located on the My Subjects page

**Trigger**
Student clicks the X button located in the same row as the subject intended for cancellation

**Main Success Scenario**
1. Student will click on the X button located in the row of the subject intended for cancellation in the Enrolled subjects table
2. Modal window Unenroll subject will appear with a preselected subject intended for cancellation
3. Student will click on the Unenroll subject button
4. UIS will remove subject from the student's list of subjects
5. Message confirming successful execution will appear

**Postconditions**
1. UIS removes the subject from the student's list of subjects and changes tables of the DB accordingly
2. Student is still on the My Subjects page
3. Message confirming successful execution appears
4. The subject is removed from the table Enrolled subjects from the My Subjects menu
5. The subject appears on the list in the table of the Other Subjects menu
6. The subject is removed from the list in the table My Exam Dates
7. The subject is removed from the list in the table Other Exam Dates
8. Teacher's View: the student disappears from the teacher's list of students enrolled on the selected subject from the table located on the menu My Subjects
9. Teacher's View: the student must not appear on the teacher's list of students enrolled on the selected subject's exam from the table located on the menu My Exam Dates
10. Teacher's View: the student must not appear on the teacher's list of the selected subject's evaluations from the table located on the menu Set Evaluation
11. Teacher's View: the student must not appear on the teacher's list of the selected subject's evaluations from the table located on the menu Evaluation Table

**Alternative Flows**
- **1a. Table has no values in it, i.e. the student is not enrolled on any subject**
  - 1a-1. The UC.04 cannot proceed

- **2a. Student sees a modal window Unenroll subject with a preselected subject intended for cancellation**
  - 2a-1. Student will choose a different subject for cancellation
  - 2a-2. Student will continue from the 3rd step of the main success scenario onwards

- **3a. Student sees a modal window Unenroll subject with a preselected subject intended for cancellation**
  - 3a-1. Student clicks on the Cancel button

  Postconditions:
  1. The menu My Subjects appears
  2. No data are overwritten or changed

- **4a. Internal error occurs in the UIS/DB during the cancellation of the subject's registration in the DB**

  Postconditions:
  1. Menu My Subjects appears
  2. Message claiming an unsuccessful execution will appear
  3. No data are overwritten or changed

**Technology and Data Variations List**
N/A

**Related Information**
- Cancellation of registration of subjects will also cancel all of the exam dates enrollments


---
