# TbUIS use cases

## UC.01 — Application login

**Context of Use**
Registered user will log into the application and based on the login name the user will be recognized either as a student or a teacher

**Scope**
UIS

**Level**
user goal

**Primary Actor**
Unlogged user

**Stakeholders and Interests**

- student: intends to log into the application
- teacher: intends to log into the application

**Constraints**

1. Users' account already exists - not possible to sign in a new account

**Preconditions**

1. User is on the UIS homepage
2. No other user is logged in - the upper bar has a black colour and on the right side there is a visible Login option of the menu

**Trigger**
User selects the Login option from the menu located on the right side of the upper bar

**Main Success Scenario**

1. User will select the Login option from the menu located on the right side of the upper bar
2. Specific Login Page form will appear
3. User will fill his/her login name that already exists (=is registered in the UIS)
4. User will enter `pass` in the password field - the universal password for all users
5. User will press the Login button

**Postconditions**

1. UIS determines whether the user is either a student or a teacher by checking the users' login name
2. Login option disappears from the top bar menu
3. Clickable first and last name of the logged-in user appear in the upper bar on the right
4. Logout option appears in the upper bar on the right
5. User with student's status sees a Student's view menu, the upper bar is orange
6. User with teacher's status sees a Teacher's view menu, the upper bar is dark green
7. Overview page appears to both Student and Teacher

**Alternative Flows**

- **5a. Selected login name does not exist in the UIS**

  Postconditions:
  1. User is not redirected from the Login Page
  2. Error message regarding an unsuccessful login attempt appears

- **5b. User enters other password than a `pass`**

  Postconditions:
  1. User is not redirected from the Login Page
  2. Error message regarding an unsuccessful login attempt appears

**Technology and Data Variations List**
N/A

**Related Information**

- Information regarding all registered users can be displayed by clicking on the Database Contents reference from the UIS homepage
- If another user needs to be added to the UIS it has to be done by importing data file into the DB (option Export/Import DB on the upper bar)

---

## UC.02 — Application logout

**Context of Use**
Logged in user is logging out of the Application

**Scope**
UIS

**Level**
user goal

**Primary Actor**
Logged in user

**Stakeholders and Interests**

- student: intends to log out of the application
- teacher: intends to log out of the application

**Constraints**
N/A

**Preconditions**

1. User is logged in - the right side of the upper bar displays the Logout option

**Trigger**
User clicks on the Login option on the menu located on the right side of the upper bar

**Main Success Scenario**

1. User will click on the Logout option on the menu located on the right side of the upper bar
2. Background colour of the upper bar will change to black
3. Login Page will appear
4. Message confirming a successful execution will appear

**Postconditions**

1. Colour of the upper bar changes to black
2. First and last names disappear from the upper bar menu
3. Logout option disappears from the upper bar menu
4. Login option appears in the right side of the upper bar
5. Login Page page appears
6. Message confirming a successful execution appears

**Alternative Flows**
N/A

**Technology and Data Variations List**
N/A

**Related Information**
N/A

---

## UC.03 — Change of user's personal data

**Context of Use**
Logged in user can change his/her first name and/or last name and/or email

**Scope**
UIS

**Level**
user goal

**Primary Actor**
Logged in user

**Stakeholders and Interests**

- student: intends to change his/her personal data
- teacher: intends to change his/her personal data

**Constraints**

1. First name must have at least 2 and not more than 30 characters
2. Last name must have at least 2 and not more than 30 characters
3. Email must have at least 8 and not more than 40 characters

**Preconditions**

1. User is already logged in to the UIS
2. User is located on the Overview page

**Trigger**
User edits one of his/her entries or the combination of them

**Main Success Scenario**

1. User will change data in the First name entry
2. User will change data in the Last name entry
3. User will change data in the Email entry
4. User will press the Update button

**Postconditions**

1. UIS saves changes and changes entries in the DB
2. User is still on the Overview page
3. Message confirming successful execution appears
4. If the user changed his/her first and/or last name, changes appear on the upper bar

**Alternative Flows**

- **1a. Entered first name has less than 2 characters**

  Postconditions:
  1. User is still on the Overview page
  2. Message notifying an unsuccessful execution appears
  3. No data are overwritten or changed

- **1b. Entered first name has more than 30 characters**

  Postconditions:
  1. User is still on the Overview page
  2. Message notifying an unsuccessful execution appears
  3. No data are overwritten or changed

- **2a. Entered last name has less than 2 characters**

  Postconditions:
  1. User is still on the Overview page
  2. Message notifying an unsuccessful execution appears
  3. No data are overwritten or changed

- **2b. Entered last name has more than 30 characters**

  Postconditions:
  1. User is still on the Overview page
  2. Message notifying an unsuccessful execution appears
  3. No data are overwritten or changed

- **3a. Entered email has less than 8 characters**

  Postconditions:
  1. User is still on the Overview page
  2. Message notifying an unsuccessful execution appears
  3. No data are overwritten or changed

- **3b. Entered email has more than 40 characters**

  Postconditions:
  1. User is still on the Overview page
  2. Message notifying an unsuccessful execution appears
  3. No data are overwritten or changed

**Technology and Data Variations List**
N/A

**Related Information**

- Overview page is visually and functionally identical for both the student and the teacher

---

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

## UC.05 — Displays subjects with passed examination

**Context of Use**
Summarized information about all subjects with successful examination and their evaluations

**Scope**
UIS

**Level**
subfunction

**Primary Actor**
student

**Stakeholders and Interests**

- student: intends to get the summarized information about completed subjects including the sum of all credits he/she achieved

**Constraints**

1. Activity is only available in the menu My Subjects

**Preconditions**

1. Student is already logged in to the UIS

**Trigger**
Student clicks on the option My Subjects of the menu.

**Main Success Scenario**

1. Student clicks on the option My Subjects of the menu

**Postconditions**

1. Table Completed Subjects is displayed with a sum of achieved credits and a list of completed subjects with evaluation of all exam terms
2. No data are overwritten or changed

**Alternative Flows**

- **1a. Student has not completed any subject yet**

  Postconditions:
  1. Header of the table displays: 0 Total Credits
  2. Message No records appears in the table

**Technology and Data Variations List**
N/A

**Related Information**

- Completed subjects are listed alphabetically

---

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

## UC.07 — Cancellation of registered exam date

**Context of Use**
Student unregisters his/her exam date for the selected subject

**Scope**
UIS

**Level**
user goal

**Primary Actor**
student

**Stakeholders and Interests**

- student: intends to unregister his/her exam date for the selected subject

**Constraints**
N/A

**Preconditions**

1. Student is already logged in to the UIS
2. Student is on the page My Exam Dates

**Trigger**
Student clicks the button Unregister in the selected subject's row with an assigned date for an examination

**Main Success Scenario**

1. Student clicks on the button Unregister in the selected subject's row with an assigned date for an examination
2. UIS will remove the date of examination from the student's list of date for the selected subject
3. Message confirming a successful execution will appear

**Postconditions**

1. UIS removes the date of examination from the student's list of exam dates for the selected subject and edits its DB and its tables accordingly
2. Student is still on the page My Exam Dates
3. Message confirming a successful execution appears
4. Subject is removed from the list in the table under the menu My Exam Dates
5. The removed date appears in the sub-table under the menu Other Exam Dates
6. Teacher's View: the student disappears from the teacher's list of students enrolled on the selected subject's exam from the table located on the menu My Exam Dates
7. Teacher's View: the student disappears from the teacher's list of the selected subject's evaluations from the table located on the menu Set Evaluation
8. Teacher's View: the student disappears from the teacher's list of the selected subject's evaluations from the table located on the menu Evaluation Table

**Alternative Flows**

- **1a. Table has no entries, i.e. student has not assigned any exam date for yet**
  - 1a-1. The UC.07 cannot proceed

- **2a. Internal error occurs in the UIS/DB during cancellation of the subject's exam date registration in the DB**

  Postconditions:
  1. Student is still on the page My exam dates
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

**Technology and Data Variations List**
N/A

**Related Information**

- Listed subjects have their specific exam date assigned

---

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

## UC.09 — Displays all examination participants - classmates

**Context of Use**
Summarized overview of all students registered for the date of an examination for a specific subject ("participants"), i.e. the student's classmates

**Scope**
UIS

**Level**
subfunction

**Primary Actor**
student

**Stakeholders and Interests**

- student: intends to get a list of his/her classmates for the exam date

**Constraints**

1. Activity is available only from the menus My Exam Dates and Other Exam Dates

**Preconditions**

1. Student is already logged in to the UIS
2. Student is either on the Other Exam Dates page or the My Exam Dates page

**Trigger**
Student clicks on the button Participants for the selected subject

**Main Success Scenario**

1. Student clicks on the button Participants for the selected subject

**Postconditions**

1. Modal window Exam Date Participants is displayed with a list of participants of an examination
2. No data are overwritten or changed

**Alternative Flows**

- **1a. No student is registered for the exam date**

  Postconditions:
  1. Table of the modal window shows the No participants message

**Technology and Data Variations List**
N/A

**Related Information**

- Modal window is can be closed via the Close button
- List sorts students alphabetically by their last name
- Similar functionality is displayed in UC.13 on the teacher's end

---

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

## UC.11 — Displays students registered in the subject

**Context of Use**
Summarized list of all students attending the specific subject

**Scope**
UIS

**Level**
subfunction

**Primary Actor**
teacher

**Stakeholders and Interests**

- teacher: intends to get a list of all students attending the subject

**Constraints**
N/A

**Preconditions**

1. Teacher is already logged in to the UIS
2. Teacher is on the page My Subjects

**Trigger**
Teacher clicks on the button Students for the specific subject

**Main Success Scenario**

1. Teacher clicks on the button Students for the specific subject

**Postconditions**

1. The modal window List of students appears
2. No data are overwritten or changed

**Alternative Flows**

- **1a. No student attends the subject**

  Postconditions:
  1. The message in the table from the modal window shows the No students message

**Technology and Data Variations List**
N/A

**Related Information**

- The modal window can be closed via the button Close
- Students are listed alphabetically by their last name

---

## UC.12 — Cancellation of the exam date

**Context of Use**
Teacher cancels the exam date for his/her subject

**Scope**
UIS

**Level**
user goal

**Primary Actor**
teacher

**Stakeholders and Interests**

- teacher: intends to cancel the exam date of his/her subject

**Constraints**

1. Only a exam date without graded students can be canceled

**Preconditions**

1. Teacher is already logged in to the UIS
2. Teacher is on the page My Exam Dates

**Trigger**
Teacher clicks on the button X in the row of the exam date

**Main Success Scenario**

1. Teacher clicks on the button X in the row of the exam date in the subject's sub-table
2. UIS will remove the exam date from the teacher's list of terms for the selected subject
3. Message confirming a successful execution will appear

**Postconditions**

1. Teacher is still on the page My Exam Dates
2. UIS removes the exam date from the teacher's list of terms for the selected subject and changes the DB and its tables accordingly
3. Message confirming a successful execution appears
4. The exam date is removed from the list in the sub-table in the menu My Exam Dates
5. The exam date is removed from the list in the menu Set Evaluation
6. The exam date is removed from the list in the menu Evaluation Table
7. Student's View: for every student with the subject enrolled the teacher and the cancelled term have disappeared on the sub-table of the subject in the menu Other Exam Dates

**Alternative Flows**

- **1a. Table has no entries, i.e. the teacher does not teach any subject at the moment**
  - 1a-1. The UC.12 cannot proceed

- **1b. Subject has empty sub-table i.e. the teacher does teach this subject but no exam dates have not been announced yet**
  - 1b-1. The UC.12 cannot proceed

- **1c. Teacher intends to cancel the exam date that has at least one student attending it**
  - 1c-1. Modal JS window will appear claiming that there are students registered in this exam term
  - 1c-2. Teacher will click on the button Cancel/Zrušit

  Postconditions:
  1. The screen of the menu My Exam Dates is still on
  2. No data are overwritten or changed

- **1d. Teacher intends to cancel the exam date that has at least one student attending it**
  - 1d-1. A modal JS window will appear claiming that there are students registered in this exam term
  - 1d-2. Teacher will click on the button OK

  Postconditions:
  1. The main success scenario continues from the step 2 onwards

- **1e. Buttons X are disabled for every exam date that has at least one student attending and at least one student on this exam date was already graded**
  - 1e-1. The UC.12 cannot proceed

- **2a. Internal error occurs in the UIS/DB during the cancellation of the subject's exam date in the DB**

  Postconditions:
  1. Page My Exam Dates is still displayed
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

**Technology and Data Variations List**
N/A

**Related Information**

- All of the taught subjects are displayed in sub-tables together with their exam terms
- Teacher can cancel any exam date with students already registered on it if no student has been graded on this exam date yet. These students have their term automatically cancelled.

---

## UC.13 — Displays all examination participants

**Context of Use**
An overview of all students registered for the date of an examination for a specific subject ("participants")

**Scope**
UIS

**Level**
subfunction

**Primary Actor**
teacher

**Stakeholders and Interests**

- teacher: intends to get a list of participants of the exam date

**Constraints**
N/A

**Preconditions**

1. Teacher is already logged in to the UIS
2. Teacher is on the page My Exam Dates

**Trigger**
Teacher clicks the button

**Main Success Scenario**

1. Teacher clicks on the button

**Postconditions**

1. Modal window Exam Date Participants is displayed with a list of the examination participants
2. No data are overwritten or changed

**Alternative Flows**

- **1a. No student has registered for the exam date**

  Postconditions:
  1. Table in a modal window will display: No participants

**Technology and Data Variations List**

1. Every student has clickable button Grade, which will launch UC.15

**Related Information**

- Modal window can be closed via the button Close
- List sorts students alphabetically by their last name
- Similar to the UC.09 function-wise from the student's side

---

## UC.14 — Announcement of a new exam date

**Context of Use**
Teacher announces a new exam date for his/her subject

**Scope**
UIS

**Level**
user goal

**Primary Actor**
teacher

**Stakeholders and Interests**

- teacher: intends to announce a new exam date for a subject he/she teaches

**Constraints**

1. New term can only be announced for a subject the teacher teaches
2. Single subject can have maximum of 3 exam dates announced by a single teacher
3. Number of possible participants cannot be lower than 1 and higher than 10
4. The exam date cannot be announced for a date that has already passed
5. The time between the last exam date and newly announced exam date has to be at least 24 hours
6. The exam date must be written down in `yyyy-MM-dd HH:mm` format

**Preconditions**

1. Teacher is already logged in to the UIS
2. Teacher is on the page My Exam Dates

**Trigger**
Teacher enters values and entries in the form

**Main Success Scenario**

1. Teacher selects the subject from the menu of subjects he/she teaches
2. Teacher enters a maximum number of examination participants
3. Teacher enters the exam date according to the formula from a place holder
4. Teacher clicks on the button Save new exam date
5. UIS will enter the examination term to the teacher's list of terms for the selected subject
6. Message confirming a successful execution will appear

**Postconditions**

1. UIS adds the exam date from the teacher's list of terms for the selected subject and changes the DB and its tables accordingly
2. Teacher is still on the page New Exam Dates
3. Message confirming a successful execution appears
4. The exam date is added to the list in the sub-table in the menu My Exam Dates
5. The exam date is added to the list in the menu Set Evaluation
6. The exam date is added to the list in the menu Evaluation Table
7. Student's View: to every student who enrolled in the subject the teacher and the exam term have appeared on the sub-table of the subject in the menu Other Exam Dates

**Alternative Flows**

- **1a. Entry form is not displayed and instead a warning reading Warning! No taught subjects is shown, i.e. the teacher does not teach any subject at the moment**
  - 1a-1. The UC.14 cannot proceed

- **1b. Teacher, without any previous activity, clicks the button Save new exam date**

  Postconditions:
  1. Teacher is still on the page New Exam Dates
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed
  4. Entry form has predefined values as its entries

- **1c. Teacher intends to select a subject that already has all 3 exam dates announced. These subjects are not listed in the dropdown menu**
  - 1c-1. The UC.14 cannot proceed

- **2a. Teacher sets a maximum of participants as less than 1**
  - 2a-1. Teacher enters the exam date according the formula from place holder
  - 2a-2. Teacher clicks on the button Save new exam date

  Postconditions:
  1. Teacher is still on the page New Exam Dates
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed
  4. Entry form has predefined values as its entries

- **2b. Teacher sets a maximum of participants as more than 10**
  - 2b-1. Teacher enters the exam date according the formula from place holder
  - 2b-2. Teacher clicks on the button Save new exam date

  Postconditions:
  1. Teacher is still on the page New Exam Dates
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed
  4. Entry form has predefined values as its entries

- **3a. Teacher sets the first exam date as a date that has already passed**
  - 3a-1. Teacher clicks on the button Save new exam date

  Postconditions:
  1. Teacher is still on the page New Exam Dates
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed
  4. Entry form has predefined values as its entries

- **3b. Teacher announces an exam date that is to take place in less than 24 hours after previous one**
  - 3b-1. Teacher clicks on the button Save new exam date

  Postconditions:
  1. Teacher is still on the page New Exam Dates
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed
  4. Entry form has predefined values as its entries

- **3c. Teacher enters the date in incorrect format**
  - 3c-1. Teacher clicks on the button Save new exam date

  Postconditions:
  1. Teacher is still on the page New Exam Dates
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed
  4. Entry form has predefined values as its entries

- **5a. Internal error occurs in the UIS/DB during the announcement of the subject's exam date in the DB**

  Postconditions:
  1. Teacher is still on the page New Exam Dates
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

**Technology and Data Variations List**

1. Teacher enters this page from the menu My Subjects by clicking on the button New exam date (see UC.10); in the list there is predefined (disabled) selected subject and UC.14 will proceed from step 2 of the main success scenario.

**Related Information**

- After the selection of New Exam Dates the form has predefined entries.
- First (alphabetically) of taught subjects is chosen
- Capacity of participants is predefined as 1
- Placeholder `yyyy-MM-dd HH:mm` is displayed

---

## UC.15 — Enters the examination evaluation

**Context of Use**
Teacher enters the examination evaluation of the selected student for the selected exam date he/she teaches

**Scope**
UIS

**Level**
user goal

**Primary Actor**
teacher

**Stakeholders and Interests**

- teacher: intends to enter the examination evaluation of a student

**Constraints**
N/A

**Preconditions**

1. Teacher is already logged in to the UIS
2. Teacher is on the page Set Evaluation

**Trigger**
Teacher enters values and entries to the form

**Main Success Scenario**

1. Teacher selects the desired subject and exam date from the menu
2. Teacher selects the desired student from the dropdown menu
3. Teacher selects the desired evaluation from the dropdown menu
4. Teacher clicks on the button Save evaluation
5. UIS will enter the student's result for the selected subject
6. Message confirming a successful execution will appear

**Postconditions**

1. UIS adds the results to the student for the selected subject and edits its DB and its tables accordingly
2. Teacher is still on page Set Evaluation
3. Message confirming a successful execution appears
4. Appropriate subject and the exam date remain selected in the dropdown menu
5. The student disappears from the list in the dropdown menu
6. Evaluation A is predefined in the dropdown menu
7. If the student scored A-E (i.e. he/she passed), he/she is removed from the list in the menu My Subjects
8. If the student scored F (i.e. he/she did not pass), he/she remains on the list in the menu My Subjects
9. The student disappears from the list of examination participans in the menu My Exam Dates
10. The evaluation will appear by the student in the menu Evaluation Table with the filter Includes students with already set grade turned on
11. Student's View: regardless on the evaluation, the subject disappears from the table in the menu My Exam Dates
12. Student's View: if the student scored A-E (i.e. he/she passed), the subject is removed from the table Enrolled Subjects in he menu My Subjects
13. Student's View: if the student scored A-E (i.e. he/she passed), credits are added to the amount in the header of the table Completed Subjects in the menu My Subjects
14. Student's View: if the student scored A-E (i.e. he/she passed), the subject appears with the achieved score in the table Completed Subjects in the menu My Subjects
15. Student's View: if the student scored A-E (i.e. he/she passed), the subject disappears from the table in the menu Other Exam Dates
16. Student's View: if the student scored F (i.e. he/she did not pass), the subject remains in the table Enrolled Subjects in the menu My Subjects
17. Student's View: if the student scored F (i.e. he/she did not pass), the subject remains in the table in the menu Other Exam Dates

**Alternative Flows**

- **1a. No entry form is displayed and instead there is a message reading: Warning! No exam dates, i.e. teacher does not have any announced exam dates at the moment**
  - 1a-1. UC.15 cannot proceed

- **1b. Teacher chooses an exam date without any students registered**

  Postconditions:
  1. Teacher is still on page Set Evaluation
  2. Entry form displays: No student is registered on this exam date!
  3. The button Save evaluation is disabled

- **4a. If the evaluated student is the last student registered on this exam date**

  Postconditions:
  1. Conditions 1-4 and 6-16 of the main postcondition list are now enforced
  2. Entry form displays: No student is registered on this exam date!
  3. Button Save evaluation is disabled

**Technology and Data Variations List**

1. Teacher accessed this page from the menu My Exam Dates of the modal window Participants by clicking the button Grade (see UC.13); in the selection list there is a predefined (disabled) subject and the exam date and the evaluated student, the program proceeds with step 3 of main scenario onwards

**Related Information**

- One subject can be taught by up to two teachers and each one of them can announce up to 3 exam dates. Teacher can only evaluate students registered on the exam date announced by him/her.
- After selecting the item from the menu Set Evaluation the entry form has predefined entries
- One of the taught subject (selected randomly) will appear with a exam date
- The first of the participans is selected (in order of the date of registration on exam date)
- Score A is selected

---

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

## UC.18 — Displays the list of teachers and subjects they teach

**Context of Use**
Overview of teachers and subjects they teach

**Scope**
UIS

**Level**
user goal

**Primary Actor**
teacher

**Stakeholders and Interests**

- teacher: intends to get summarized information about the teaching staff

**Constraints**
N/A

**Preconditions**

1. Teacher is already logged in to the UIS

**Trigger**
Teacher clicks on the option List of All Teachers of the menu

**Main Success Scenario**

1. Teacher clicks on the option of the menu List of All Teachers

**Postconditions**

1. Table List of All Teachers is displayed
2. No data are overwritten or saved - no changes occur

**Alternative Flows**

- **1a. There is no subject in the UIS**

  Postconditions:
  1. Column of subjects is empty

**Technology and Data Variations List**
N/A

**Related Information**

- Teachers are listed alphabetically
- Subjects they teach are also listed alphabetically

---

## UC.19 — Restoration of the database

**Context of Use**
Unlogged user restores DB's into the default state, usually before proceeding to the tests

**Scope**
UIS

**Level**
subfunction

**Primary Actor**
unlogged user

**Stakeholders and Interests**

- logged off user: intends to set the database's state to default

**Constraints**
N/A

**Preconditions**

1. No one is logged in the UIS - the upper menu contains the option Restore DB

**Trigger**
Unlogged user clicks on the option Restore DB of the menu

**Main Success Scenario**

1. Unlogged user clicks on the option Restore DB of the menu
2. Message confirming a successful execution will appear

**Postconditions**

1. User is on the page University information System (Home page)
2. Message confirming a successful execution appears

**Alternative Flows**
N/A

**Technology and Data Variations List**
N/A

**Related Information**

- Default content of the database is displayable by clicking the reference Database content

---

## UC.20 — Displays information about system's abilities

**Context of Use**
Unlogged user gets information about existing use-cases, contents of databes and restrictions in the UIS

**Scope**
UIS

**Level**
subfunction

**Primary Actor**
unlogged user

**Stakeholders and Interests**

- logged off user: intends to get information about the UIS

**Constraints**
N/A

**Preconditions**

1. No one is logged in to the UIS
2. User is on the page University information System (Home page)

**Trigger**
Unlogged user clicks on one of the options on the list on the lower left part of the UI/display

**Main Success Scenario**

1. Unlogged user clicks on one of the following options: Application use-cases, Database content, Application constraints
2. Desired information will display

**Postconditions**

1. Desired information is displayed

**Alternative Flows**
N/A

**Technology and Data Variations List**
N/A

**Related Information**
N/A

---

## UC.21 — Export of the database

**Context of Use**
Unlogged user saves the current content of the database as an external XML/JSON file

**Scope**
UIS

**Level**
subfunction

**Primary Actor**
unlogged user

**Stakeholders and Interests**

- logged off user: intends to export the current content of the database

**Constraints**
N/A

**Preconditions**

1. > No one is logged in to the UIS - the upper menu has the option Export/Import DB

**Trigger**
Unlogged user clicks on the Export/Import DB item on the menu

**Main Success Scenario**

1. Unlogged user clicks on the Export/Import DB item on the menu
2. Unlogged user chooses either a XML or a JSON file in the Export DB to file form
3. Unlogged user clicks on the button Export
4. Message of a web browser will appear with input for specifying the location of the file
5. Web browser will save the file with a predefined name (e.g. `2019-12-02_18-11_DB-export.xml`) to the desired directory

**Postconditions**

1. User is still on the page Export/Import DB

**Alternative Flows**
N/A

**Technology and Data Variations List**
N/A

**Related Information**
N/A

---

## UC.22 — Import of the database

**Context of Use**
Unlogged user rewriters the current content of the database with the content of external XML or JSON file

**Scope**
UIS

**Level**
subfunction

**Primary Actor**
Unlogged user

**Stakeholders and Interests**

- logged off user: intends to set the content of the database to desired values

**Constraints**
N/A

**Preconditions**

1. No one is logged in to the UIS - the upper menu has the option Export/Import DB

**Trigger**
Unlogged user clicks on the Export/Import DB item on the menu

**Main Success Scenario**

1. Unlogged user clicks on the Export/Import DB item on the menu
2. Unlogged user clicks on the Browse (or its bilingual equivalent) option in the form Import data into DB)
3. Unlogged user chooses the desired XML or JSON file
4. Unlogged user clicks on the button Import
5. Message confirming a successful execution will appear

**Postconditions**

1. User is still on the page Export/Import DB
2. Message confirming a successful execution appears

**Alternative Flows**

- **1a. Unlogged user clicks on the button Import**

  Postconditions:
  1. User is still on the page Export/Import DB
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

- **4a. The imported file does not have a correct format or content**

  Postconditions:
  1. User is still on the page Export/Import DB
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

- **4b. Internal error occurs in the UIS/DB during the setting of the new DB content**

  Postconditions:
  1. User is still on the page Export/Import DB
  2. Message claiming an unsuccessful execution appears
  3. No data are overwritten or changed

**Technology and Data Variations List**
N/A

**Related Information**
N/A
