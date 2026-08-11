## UC.06 — Subject enrollment

**Context of Use**
Student enrolls to one of the so far not enrolled subjects

**Scope**
UIS

**Level**
user goal

**Primary Actor**
student

**Stakeholders and Interests**

- student: intends to enroll in a subject

**Constraints**

1. Student cannot enroll in any subject which is not taught yet
2. Student cannot enroll in more than 7 subjects

**Preconditions**

1. Student is logged in to the UIS
2. Student is on the page Other Subjects

**Trigger**
Student clicks on the Enroll button from the row of the subject intended for enrollment

**Main Success Scenario**

1. Student clicks on the Enroll button from the row of the subject intended for enrollment
2. UIS system will add the selected subject on the student's list of enrolled subjects
3. Message confirming a successful execution will appear

**Postconditions**

1. UIS system will add the selected subject on the student's list of enrolled subjects and will change the tables of the DB accordingly
2. Student is still on the page Other Subjects
3. Message confirming a successful execution will appear
4. The subject will be removed from the table under the menu Other Subjects
5. The subject will be added to the list on the table Enrolled Subjects under the menu My Subjects
6. The subject will be added to the table under the menu Other Exam Dates
7. Teacher's View: the student will appear on the teacher's list of students enrolled in the selected subject from the table located on the menu My Subjects

**Alternative Flows**

- **1a. Table has no values in it, i.e. the student is already enrolled in all of the existing subjects**
  - 1a-1. The UC.06 cannot proceed

- **1b. Button Enroll is disabled for selected subject because the subject has no assigned teacher**
  - 1b-1. The UC.06 cannot proceed

- **1c. Button Enroll is disabled for the selected subject, because student has already reached limit of assigned subjects**
  - 1c-1. The UC.06 cannot proceed

- **2a. Internal error occurs in the UIS/DB during the subject's registration in the DB**

  Postconditions:
  1. Student is still on the page Other Subjects
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

**Technology and Data Variations List**
N/A

**Related Information**

- All the enroll-able subjects are announced

---
