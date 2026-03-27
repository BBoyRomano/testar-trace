# Subject enrollment
ID: UC.06
Actor: student

## Preconditions
- Student is logged in to the UIS
- Student is on the page Other Subjects

## Main flow
1. Student clicks on the Enroll button from the row of the subject intended for enrollment
2. UIS system will add the selected subject on the student's list of enrolled subjects
3. Message confirming a successful execution will appear

## Alternative flow
1. 1a. Table has no values in it, i.e. the student is already enrolled in all of the existing subjects
2. 1a-1. The UC.06 cannot proceed
3. 1b. Button Enroll is disabled for selected subject because the subject has no assigned teacher
4. 1b-1. The UC.06 cannot proceed
5. 1c. Button Enroll is disabled for the selected subject, because student has already reached limit of assigned subjects
6. 1c-1. The UC.06 cannot proceed
7. 2a. Internal error occurs in the UIS/DB during the subject's registration in the DB
8. Postcondition: Student is still on the page Other Subjects
9. Postcondition: Message claiming an unsuccessful execution appears
10. Postcondition: No data are overwritten or changed

## Postconditions
- UIS system will add the selected subject on the student's list of enrolled subjects and will change the tables of the DB accordingly
- Student is still on the page Other Subjects
- Message confirming a successful execution will appear
- The subject will be removed from the table under the menu Other Subjects
- The subject will be added to the list on the table Enrolled Subjects under the menu My Subjects
- The subject will be added to the table under the menu Other Exam Dates
- Teacher's View: the student will appear on the teacher's list of students enrolled in the selected subject from the table located on the menu My Subjects
