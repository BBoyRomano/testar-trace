# Announcement of a new exam date
ID: UC.14
Actor: teacher

## Preconditions
- Teacher is already logged in to the UIS
- Teacher is on the page My Exam Dates

## Main flow
1. Teacher selects the subject from the menu of subjects he/she teaches
2. Teacher enters a maximum number of examination participants
3. Teacher enters the exam date according to the formula from a place holder
4. Teacher clicks on the button Save new exam date
5. UIS will enter the examination term to the teacher's list of terms for the selected subject
6. Message confirming a successful execution will appear

## Alternative flow
1. 1a. Entry form is not displayed and instead a warning reading Warning! No taught subjects is shown, i.e. the teacher does not teach any subject at the moment
2. 1a-1. The UC.14 cannot proceed
3. 1b. Teacher, without any previous activity, clicks the button Save new exam date
4. Postcondition: Teacher is still on the page New Exam Dates
5. Postcondition: Message claiming an unsuccessful execution appears
6. Postcondition: No data are overwritten or changed
7. Postcondition: Entry form has predefined values as its entries
8. 1c. Teacher intends to select a subject that already has all 3 exam dates announced. These subjects are not listed in the dropdown menu
9. 1c-1. The UC.14 cannot proceed
10. 2a. Teacher sets a maximum of participants as less than 1
11. 2a-1. Teacher enters the exam date according the formula from place holder
12. 2a-2. Teacher clicks on the button Save new exam date
13. Postcondition: Teacher is still on the page New Exam Dates
14. Postcondition: Message claiming an unsuccessful execution appears
15. Postcondition: No data are overwritten or changed
16. Postcondition: Entry form has predefined values as its entries
17. 2b. Teacher sets a maximum of participants as more than 10
18. 2b-1. Teacher enters the exam date according the formula from place holder
19. 2b-2. Teacher clicks on the button Save new exam date
20. Postcondition: Teacher is still on the page New Exam Dates
21. Postcondition: Message claiming an unsuccessful execution appears
22. Postcondition: No data are overwritten or changed
23. Postcondition: Entry form has predefined values as its entries
24. 3a. Teacher sets the first exam date as a date that has already passed
25. 3a-1. Teacher clicks on the button Save new exam date
26. Postcondition: Teacher is still on the page New Exam Dates
27. Postcondition: Message claiming an unsuccessful execution appears
28. Postcondition: No data are overwritten or changed
29. Postcondition: Entry form has predefined values as its entries
30. 3b. Teacher announces an exam date that is to take place in less than 24 hours after previous one
31. 3b-1. Teacher clicks on the button Save new exam date
32. Postcondition: Teacher is still on the page New Exam Dates
33. Postcondition: Message claiming an unsuccessful execution appears
34. Postcondition: No data are overwritten or changed
35. Postcondition: Entry form has predefined values as its entries
36. 3c. Teacher enters the date in incorrect format
37. 3c-1. Teacher clicks on the button Save new exam date
38. Postcondition: Teacher is still on the page New Exam Dates
39. Postcondition: Message claiming an unsuccessful execution appears
40. Postcondition: No data are overwritten or changed
41. Postcondition: Entry form has predefined values as its entries
42. 5a. Internal error occurs in the UIS/DB during the announcement of the subject's exam date in the DB
43. Postcondition: Teacher is still on the page New Exam Dates
44. Postcondition: Message claiming an unsuccessful execution appears
45. Postcondition: No data are overwritten or changed

## Postconditions
- UIS adds the exam date from the teacher's list of terms for the selected subject and changes the DB and its tables accordingly
- Teacher is still on the page New Exam Dates
- Message confirming a successful execution appears
- The exam date is added to the list in the sub-table in the menu My Exam Dates
- The exam date is added to the list in the menu Set Evaluation
- The exam date is added to the list in the menu Evaluation Table
- Student's View: to every student who enrolled in the subject the teacher and the exam term have appeared on the sub-table of the subject in the menu Other Exam Dates
