# Registration of a new exam date
ID: UC.08
Actor: student

## Preconditions
- Student is already logged in to the UIS
- Student is located on the page Other Exam Dates

## Main flow
1. Student will click on the button Register located in a sub-table for the selected subject with an assigned examination term
2. UIS will add the date of an examination to the student's list of dates for the selected subject
3. Message confirming a successful execution will appear

## Alternative flow
1. 1a. Table has no entries in it, i.e. the student is not enrolled on any subject
2. 1a-1. The UC.08 cannot proceed
3. 1b. Sub-tables for selected subjects have no entries, i.e. student already registered exam dates for all subjects
4. 1b-1. The UC.08 cannot proceed
5. 1c. Table has subjects in it, yet their sub-tables have no entries, i.e. teachers did not announce any dates yet
6. 1c-1. The UC.08 cannot proceed
7. 1d. Button Register is disabled and entire sub-table has a yellow background i.e. the student already registered for exam date and teacher announced dates of other examinations
8. 1d-1. The UC.08 cannot proceed
9. 1e. Button Register is disabled and the button Participants shows that this exam date has no free registration available
10. 1e-1. The UC.08 cannot proceed
11. 1f. Two teachers teach this subject and each of them can announce up to three exam dates. The student has been already graded F three times. Now the student tries to registrate to second teachers' exam date (eg. fourth student's attempt). Student clicks on button Register.
12. Postcondition: Student is still on the page Other Exam Dates
13. Postcondition: Message claiming an unsuccessful execution appears
14. Postcondition: No data are overwritten or changed
15. 2a. Internal error occurs in the UIS/DB during the subject's exam date registration in the DB
16. Postcondition: Student is still on the page Other Exam Dates
17. Postcondition: Message claiming an unsuccessful execution appears
18. Postcondition: No data are overwritten or changed

## Postconditions
- UIS adds the date of an examination to the student's list of dates for the selected subject and changes its tables in the DB accordingly
- Student is still on the page Other Exam Dates
- Message confirming a successful execution appears
- Exam date is removed from the subject's sub-table under the menu Other Exam Dates
- In case of multiple exam dates for a single subject, the selected choice has a yellow background colour
- Exam date appears with the subject on the table under the menu My Exam Dates
- Teacher's View: the student appears on the teacher's list of students enrolled on the selected subject's exam from the table located on the menu My Exam Dates
- Teacher's View: the student appears on the teacher's list of the selected subject's evaluations from the table located on the menu Set Evaluation
- Teacher's View: the student appears on the teacher's list of the selected subject's evaluations from the table located on the menu Evalutaion Table
