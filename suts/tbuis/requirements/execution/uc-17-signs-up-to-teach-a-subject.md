# Signs up to teach a subject
ID: UC.17
Actor: teacher

## Preconditions
- Teacher is already logged in to the UIS
- Teacher is on the page Others' Subjects

## Main flow
1. Teacher clicks on the button Participate in the row of the desired subject
2. UIS will add the subject to the teacher's list of subjects
3. Message confirming a successful execution will appear

## Alternative flow
1. 1a. Table has no entries, i.e. the teacher already leads sessions (or is taking a part in the sessions) of all existing subjects
2. 1a-1. The UC.17 cannot proceed
3. 1b. Teacher intends to teach subject that is already taught by two other teachers
4. 1b-1. The UC.17 cannot proceed
5. 2a. Internal error occurs in the UIS/DB during the uploading of the information in the DB
6. Postcondition: Teacher is still on the page Others' Subjects
7. Postcondition: Message claiming an unsuccessful execution appears
8. Postcondition: No data are overwritten or changed

## Postconditions
- UIS adds the subject to the teacher's list of subjects and changes the DB and its tables accordingly
- Teacher is still on the page Others' Subjects
- Message confirming a successful execution appears
- The subject disappears from the list in the menu Others' Subjects
- The subject appears in the table in the menu My Exam Dates and its' sub-table is empty (i.e. is without exam date)
- The subject appears on the list in the menu New Exam Dates
- The subject appears on the list in the menu Evaluation Table
- The subject appears under this teacher on the list in the menu List of All Teachers
- Student's View: to every student the teacher appears on the list of teachers leading the subject's sessions in the menu Other Subjects
