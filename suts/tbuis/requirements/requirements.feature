Feature: TbUIS requirements

  Scenario: UC.01 Application login
    Given User is on the UIS homepage
    And No other user is logged in - the upper bar has a black colour and on the right side there is a visible Login option of the menu
    When User selects the Login option from the menu located on the right side of the upper bar
    And User will select the Login option from the menu located on the right side of the upper bar
    And Specific Login Page form will appear
    And User will fill his/her login name that already exists (=is registered in the UIS)
    And User will enter `pass` in the password field - the universal password for all users
    And User will press the Login button
    Then UIS determines whether the user is either a student or a teacher by checking the users' login name
    And Login option disappears from the top bar menu
    And Clickable first and last name of the logged-in user appear in the upper bar on the right
    And Logout option appears in the upper bar on the right
    And User with student's status sees a Student's view menu, the upper bar is orange
    And User with teacher's status sees a Teacher's view menu, the upper bar is dark green
    And Overview page appears to both Student and Teacher

  Scenario: UC.01 5a. Selected login name does not exist in the UIS
    Given 5a. Selected login name does not exist in the UIS
    Then User is not redirected from the Login Page
    And Error message regarding an unsuccessful login attempt appears

  Scenario: UC.01 5b. User enters other password than a `pass`
    Given 5b. User enters other password than a `pass`
    Then User is not redirected from the Login Page
    And Error message regarding an unsuccessful login attempt appears

  Scenario: UC.02 Application logout
    Given User is logged in - the right side of the upper bar displays the Logout option
    When User clicks on the Login option on the menu located on the right side of the upper bar
    And User will click on the Logout option on the menu located on the right side of the upper bar
    And Background colour of the upper bar will change to black
    And Login Page will appear
    And Message confirming a successful execution will appear
    Then Colour of the upper bar changes to black
    And First and last names disappear from the upper bar menu
    And Logout option disappears from the upper bar menu
    And Login option appears in the right side of the upper bar
    And Login Page page appears
    And Message confirming a successful execution appears

  Scenario: UC.03 Change of user's personal data
    Given User is already logged in to the UIS
    And User is located on the Overview page
    When User edits one of his/her entries or the combination of them
    And User will change data in the First name entry
    And User will change data in the Last name entry
    And User will change data in the Email entry
    And User will press the Update button
    Then UIS saves changes and changes entries in the DB
    And User is still on the Overview page
    And Message confirming successful execution appears
    And If the user changed his/her first and/or last name, changes appear on the upper bar

  Scenario: UC.03 1a. Entered first name has less than 2 characters
    Given 1a. Entered first name has less than 2 characters
    Then User is still on the Overview page
    And Message notifying an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.03 1b. Entered first name has more than 30 characters
    Given 1b. Entered first name has more than 30 characters
    Then User is still on the Overview page
    And Message notifying an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.03 2a. Entered last name has less than 2 characters
    Given 2a. Entered last name has less than 2 characters
    Then User is still on the Overview page
    And Message notifying an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.03 2b. Entered last name has more than 30 characters
    Given 2b. Entered last name has more than 30 characters
    Then User is still on the Overview page
    And Message notifying an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.03 3a. Entered email has less than 8 characters
    Given 3a. Entered email has less than 8 characters
    Then User is still on the Overview page
    And Message notifying an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.03 3b. Entered email has more than 40 characters
    Given 3b. Entered email has more than 40 characters
    Then User is still on the Overview page
    And Message notifying an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.04 Cancelling the registration (enrollment) to a subject
    Given Student is logged in to the UIS
    And User is located on the My Subjects page
    When Student clicks the X button located in the same row as the subject intended for cancellation
    And Student will click on the X button located in the row of the subject intended for cancellation in the Enrolled subjects table
    And Modal window Unenroll subject will appear with a preselected subject intended for cancellation
    And Student will click on the Unenroll subject button
    And UIS will remove subject from the student's list of subjects
    And Message confirming successful execution will appear
    Then UIS removes the subject from the student's list of subjects and changes tables of the DB accordingly
    And Student is still on the My Subjects page
    And Message confirming successful execution appears
    And The subject is removed from the table Enrolled subjects from the My Subjects menu
    And The subject appears on the list in the table of the Other Subjects menu
    And The subject is removed from the list in the table My Exam Dates
    And The subject is removed from the list in the table Other Exam Dates
    And Teacher's View: the student disappears from the teacher's list of students enrolled on the selected subject from the table located on the menu My Subjects
    And Teacher's View: the student must not appear on the teacher's list of students enrolled on the selected subject's exam from the table located on the menu My Exam Dates
    And Teacher's View: the student must not appear on the teacher's list of the selected subject's evaluations from the table located on the menu Set Evaluation
    And Teacher's View: the student must not appear on the teacher's list of the selected subject's evaluations from the table located on the menu Evaluation Table

  Scenario: UC.04 1a. Table has no values in it, i.e. the student is not enrolled on any subject
    Given 1a. Table has no values in it, i.e. the student is not enrolled on any subject
    When 1a-1. The UC.04 cannot proceed
    Then N/A

  Scenario: UC.04 2a. Student sees a modal window Unenroll subject with a preselected subject intended for cancellation
    Given 2a. Student sees a modal window Unenroll subject with a preselected subject intended for cancellation
    When 2a-1. Student will choose a different subject for cancellation
    When 2a-2. Student will continue from the 3rd step of the main success scenario onwards
    Then N/A

  Scenario: UC.04 3a. Student sees a modal window Unenroll subject with a preselected subject intended for cancellation
    Given 3a. Student sees a modal window Unenroll subject with a preselected subject intended for cancellation
    When 3a-1. Student clicks on the Cancel button
    Then The menu My Subjects appears
    And No data are overwritten or changed

  Scenario: UC.04 4a. Internal error occurs in the UIS/DB during the cancellation of the subject's registration in the DB
    Given 4a. Internal error occurs in the UIS/DB during the cancellation of the subject's registration in the DB
    Then Menu My Subjects appears
    And Message claiming an unsuccessful execution will appear
    And No data are overwritten or changed

  Scenario: UC.05 Displays subjects with passed examination
    Given Student is already logged in to the UIS
    When Student clicks on the option My Subjects of the menu.
    And Student clicks on the option My Subjects of the menu
    Then Table Completed Subjects is displayed with a sum of achieved credits and a list of completed subjects with evaluation of all exam terms
    And No data are overwritten or changed

  Scenario: UC.05 1a. Student has not completed any subject yet
    Given 1a. Student has not completed any subject yet
    Then Header of the table displays: 0 Total Credits
    And Message No records appears in the table

  Scenario: UC.06 Subject enrollment
    Given Student is logged in to the UIS
    And Student is on the page Other Subjects
    When Student clicks on the Enroll button from the row of the subject intended for enrollment
    And Student clicks on the Enroll button from the row of the subject intended for enrollment
    And UIS system will add the selected subject on the student's list of enrolled subjects
    And Message confirming a successful execution will appear
    Then UIS system will add the selected subject on the student's list of enrolled subjects and will change the tables of the DB accordingly
    And Student is still on the page Other Subjects
    And Message confirming a successful execution will appear
    And The subject will be removed from the table under the menu Other Subjects
    And The subject will be added to the list on the table Enrolled Subjects under the menu My Subjects
    And The subject will be added to the table under the menu Other Exam Dates
    And Teacher's View: the student will appear on the teacher's list of students enrolled in the selected subject from the table located on the menu My Subjects

  Scenario: UC.06 1a. Table has no values in it, i.e. the student is already enrolled in all of the existing subjects
    Given 1a. Table has no values in it, i.e. the student is already enrolled in all of the existing subjects
    When 1a-1. The UC.06 cannot proceed
    Then N/A

  Scenario: UC.06 1b. Button Enroll is disabled for selected subject because the subject has no assigned teacher
    Given 1b. Button Enroll is disabled for selected subject because the subject has no assigned teacher
    When 1b-1. The UC.06 cannot proceed
    Then N/A

  Scenario: UC.06 1c. Button Enroll is disabled for the selected subject, because student has already reached limit of assigned subjects
    Given 1c. Button Enroll is disabled for the selected subject, because student has already reached limit of assigned subjects
    When 1c-1. The UC.06 cannot proceed
    Then N/A

  Scenario: UC.06 2a. Internal error occurs in the UIS/DB during the subject's registration in the DB
    Given 2a. Internal error occurs in the UIS/DB during the subject's registration in the DB
    Then Student is still on the page Other Subjects
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.07 Cancellation of registered exam date
    Given Student is already logged in to the UIS
    And Student is on the page My Exam Dates
    When Student clicks the button Unregister in the selected subject's row with an assigned date for an examination
    And Student clicks on the button Unregister in the selected subject's row with an assigned date for an examination
    And UIS will remove the date of examination from the student's list of date for the selected subject
    And Message confirming a successful execution will appear
    Then UIS removes the date of examination from the student's list of exam dates for the selected subject and edits its DB and its tables accordingly
    And Student is still on the page My Exam Dates
    And Message confirming a successful execution appears
    And Subject is removed from the list in the table under the menu My Exam Dates
    And The removed date appears in the sub-table under the menu Other Exam Dates
    And Teacher's View: the student disappears from the teacher's list of students enrolled on the selected subject's exam from the table located on the menu My Exam Dates
    And Teacher's View: the student disappears from the teacher's list of the selected subject's evaluations from the table located on the menu Set Evaluation
    And Teacher's View: the student disappears from the teacher's list of the selected subject's evaluations from the table located on the menu Evaluation Table

  Scenario: UC.07 1a. Table has no entries, i.e. student has not assigned any exam date for yet
    Given 1a. Table has no entries, i.e. student has not assigned any exam date for yet
    When 1a-1. The UC.07 cannot proceed
    Then N/A

  Scenario: UC.07 2a. Internal error occurs in the UIS/DB during cancellation of the subject's exam date registration in the DB
    Given 2a. Internal error occurs in the UIS/DB during cancellation of the subject's exam date registration in the DB
    Then Student is still on the page My exam dates
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.08 Registration of a new exam date
    Given Student is already logged in to the UIS
    And Student is located on the page Other Exam Dates
    When Student clicks on the button Register located in a sub-table for the selected subject with an assigned exam date
    And Student will click on the button Register located in a sub-table for the selected subject with an assigned examination term
    And UIS will add the date of an examination to the student's list of dates for the selected subject
    And Message confirming a successful execution will appear
    Then UIS adds the date of an examination to the student's list of dates for the selected subject and changes its tables in the DB accordingly
    And Student is still on the page Other Exam Dates
    And Message confirming a successful execution appears
    And Exam date is removed from the subject's sub-table under the menu Other Exam Dates
    And In case of multiple exam dates for a single subject, the selected choice has a yellow background colour
    And Exam date appears with the subject on the table under the menu My Exam Dates
    And Teacher's View: the student appears on the teacher's list of students enrolled on the selected subject's exam from the table located on the menu My Exam Dates
    And Teacher's View: the student appears on the teacher's list of the selected subject's evaluations from the table located on the menu Set Evaluation
    And Teacher's View: the student appears on the teacher's list of the selected subject's evaluations from the table located on the menu Evalutaion Table

  Scenario: UC.08 1a. Table has no entries in it, i.e. the student is not enrolled on any subject
    Given 1a. Table has no entries in it, i.e. the student is not enrolled on any subject
    When 1a-1. The UC.08 cannot proceed
    Then N/A

  Scenario: UC.08 1b. Sub-tables for selected subjects have no entries, i.e. student already registered exam dates for all subjects
    Given 1b. Sub-tables for selected subjects have no entries, i.e. student already registered exam dates for all subjects
    When 1b-1. The UC.08 cannot proceed
    Then N/A

  Scenario: UC.08 1c. Table has subjects in it, yet their sub-tables have no entries, i.e. teachers did not announce any dates yet
    Given 1c. Table has subjects in it, yet their sub-tables have no entries, i.e. teachers did not announce any dates yet
    When 1c-1. The UC.08 cannot proceed
    Then N/A

  Scenario: UC.08 1d. Button Register is disabled and entire sub-table has a yellow background i.e. the student already registered for exam date and teacher announced dates of other examinations
    Given 1d. Button Register is disabled and entire sub-table has a yellow background i.e. the student already registered for exam date and teacher announced dates of other examinations
    When 1d-1. The UC.08 cannot proceed
    Then N/A

  Scenario: UC.08 1e. Button Register is disabled and the button Participants shows that this exam date has no free registration available
    Given 1e. Button Register is disabled and the button Participants shows that this exam date has no free registration available
    When 1e-1. The UC.08 cannot proceed
    Then N/A

  Scenario: UC.08 1f. Two teachers teach this subject and each of them can announce up to three exam dates. The student has been already graded F three times. Now the student tries to registrate to second teachers' exam date (eg. fourth student's attempt). Student clicks on button Register.
    Given 1f. Two teachers teach this subject and each of them can announce up to three exam dates. The student has been already graded F three times. Now the student tries to registrate to second teachers' exam date (eg. fourth student's attempt). Student clicks on button Register.
    Then Student is still on the page Other Exam Dates
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.08 2a. Internal error occurs in the UIS/DB during the subject's exam date registration in the DB
    Given 2a. Internal error occurs in the UIS/DB during the subject's exam date registration in the DB
    Then Student is still on the page Other Exam Dates
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.09 Displays all examination participants - classmates
    Given Student is already logged in to the UIS
    And Student is either on the Other Exam Dates page or the My Exam Dates page
    When Student clicks on the button Participants for the selected subject
    And Student clicks on the button Participants for the selected subject
    Then Modal window Exam Date Participants is displayed with a list of participants of an examination
    And No data are overwritten or changed

  Scenario: UC.09 1a. No student is registered for the exam date
    Given 1a. No student is registered for the exam date
    Then Table of the modal window shows the No participants message

  Scenario: UC.10 Cancellation of registered subject
    Given Teacher is already logged in to the UIS
    And Teacher is on the page My Subjects
    When Teacher clicks on the button Remove located in the row of the subject intended for cancellation
    And Teacher clicks on the button Remove located in the row of the subject intended for cancellation
    And UIS will remove the subject from the teacher's subject list
    And Message confirming a successful execution will appear
    Then UIS removes the subject from the teacher's list of subjects and changes the DB and its tables accordingly
    And Teacher is still on the page My Subjects
    And Message confirming a successful execution appears
    And The subject is removed from the list in the menu My Subjects
    And The subject is removed from the list in the menu My Exam Dates
    And The subject is removed from the list in the menu New Exam Dates
    And The subject is removed from the list in the menu Set Evaluation
    And The subject is removed from the list in the menu Evaluation Table
    And The subject appears on the list in the menu Others' Subjects
    And The subject is removed from the teachers' list of subjects in the menu List of All Teachers for the specific teacher
    And Student's View: students must not find the removing teacher's name for the subject in the menu Other Subjects
    And Student's View: students must not find the removing teacher's name on the list of examining teachers for the selected subject in the menu Other Exam Dates

  Scenario: UC.10 1a. Table has no entries, i.e. the teacher in not teaching any subjects at the moment
    Given 1a. Table has no entries, i.e. the teacher in not teaching any subjects at the moment
    When 1a-1. The UC.10 cannot proceed
    Then N/A

  Scenario: UC.10 1b. Buttons Remove are disabled for every subject that has at least one student enrolled
    Given 1b. Buttons Remove are disabled for every subject that has at least one student enrolled
    When 1b-1. The UC.10 cannot proceed
    Then N/A

  Scenario: UC.10 2a. Internal error occurs in the UIS/DB during the cancellation of the subject in the DB
    Given 2a. Internal error occurs in the UIS/DB during the cancellation of the subject in the DB
    Then Teacher remains on the page My Subjects
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.11 Displays students registered in the subject
    Given Teacher is already logged in to the UIS
    And Teacher is on the page My Subjects
    When Teacher clicks on the button Students for the specific subject
    And Teacher clicks on the button Students for the specific subject
    Then The modal window List of students appears
    And No data are overwritten or changed

  Scenario: UC.11 1a. No student attends the subject
    Given 1a. No student attends the subject
    Then The message in the table from the modal window shows the No students message

  Scenario: UC.12 Cancellation of the exam date
    Given Teacher is already logged in to the UIS
    And Teacher is on the page My Exam Dates
    When Teacher clicks on the button X in the row of the exam date
    And Teacher clicks on the button X in the row of the exam date in the subject's sub-table
    And UIS will remove the exam date from the teacher's list of terms for the selected subject
    And Message confirming a successful execution will appear
    Then Teacher is still on the page My Exam Dates
    And UIS removes the exam date from the teacher's list of terms for the selected subject and changes the DB and its tables accordingly
    And Message confirming a successful execution appears
    And The exam date is removed from the list in the sub-table in the menu My Exam Dates
    And The exam date is removed from the list in the menu Set Evaluation
    And The exam date is removed from the list in the menu Evaluation Table
    And Student's View: for every student with the subject enrolled the teacher and the cancelled term have disappeared on the sub-table of the subject in the menu Other Exam Dates

  Scenario: UC.12 1a. Table has no entries, i.e. the teacher does not teach any subject at the moment
    Given 1a. Table has no entries, i.e. the teacher does not teach any subject at the moment
    When 1a-1. The UC.12 cannot proceed
    Then N/A

  Scenario: UC.12 1b. Subject has empty sub-table i.e. the teacher does teach this subject but no exam dates have not been announced yet
    Given 1b. Subject has empty sub-table i.e. the teacher does teach this subject but no exam dates have not been announced yet
    When 1b-1. The UC.12 cannot proceed
    Then N/A

  Scenario: UC.12 1c. Teacher intends to cancel the exam date that has at least one student attending it
    Given 1c. Teacher intends to cancel the exam date that has at least one student attending it
    When 1c-1. Modal JS window will appear claiming that there are students registered in this exam term
    When 1c-2. Teacher will click on the button Cancel/Zrušit
    Then The screen of the menu My Exam Dates is still on
    And No data are overwritten or changed

  Scenario: UC.12 1d. Teacher intends to cancel the exam date that has at least one student attending it
    Given 1d. Teacher intends to cancel the exam date that has at least one student attending it
    When 1d-1. A modal JS window will appear claiming that there are students registered in this exam term
    When 1d-2. Teacher will click on the button OK
    Then The main success scenario continues from the step 2 onwards

  Scenario: UC.12 1e. Buttons X are disabled for every exam date that has at least one student attending and at least one student on this exam date was already graded
    Given 1e. Buttons X are disabled for every exam date that has at least one student attending and at least one student on this exam date was already graded
    When 1e-1. The UC.12 cannot proceed
    Then N/A

  Scenario: UC.12 2a. Internal error occurs in the UIS/DB during the cancellation of the subject's exam date in the DB
    Given 2a. Internal error occurs in the UIS/DB during the cancellation of the subject's exam date in the DB
    Then Page My Exam Dates is still displayed
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.13 Displays all examination participants
    Given Teacher is already logged in to the UIS
    And Teacher is on the page My Exam Dates
    When Teacher clicks the button
    And Teacher clicks on the button
    Then Modal window Exam Date Participants is displayed with a list of the examination participants
    And No data are overwritten or changed

  Scenario: UC.13 1a. No student has registered for the exam date
    Given 1a. No student has registered for the exam date
    Then Table in a modal window will display: No participants

  Scenario: UC.14 Announcement of a new exam date
    Given Teacher is already logged in to the UIS
    And Teacher is on the page My Exam Dates
    When Teacher enters values and entries in the form
    And Teacher selects the subject from the menu of subjects he/she teaches
    And Teacher enters a maximum number of examination participants
    And Teacher enters the exam date according to the formula from a place holder
    And Teacher clicks on the button Save new exam date
    And UIS will enter the examination term to the teacher's list of terms for the selected subject
    And Message confirming a successful execution will appear
    Then UIS adds the exam date from the teacher's list of terms for the selected subject and changes the DB and its tables accordingly
    And Teacher is still on the page New Exam Dates
    And Message confirming a successful execution appears
    And The exam date is added to the list in the sub-table in the menu My Exam Dates
    And The exam date is added to the list in the menu Set Evaluation
    And The exam date is added to the list in the menu Evaluation Table
    And Student's View: to every student who enrolled in the subject the teacher and the exam term have appeared on the sub-table of the subject in the menu Other Exam Dates

  Scenario: UC.14 1a. Entry form is not displayed and instead a warning reading Warning! No taught subjects is shown, i.e. the teacher does not teach any subject at the moment
    Given 1a. Entry form is not displayed and instead a warning reading Warning! No taught subjects is shown, i.e. the teacher does not teach any subject at the moment
    When 1a-1. The UC.14 cannot proceed
    Then N/A

  Scenario: UC.14 1b. Teacher, without any previous activity, clicks the button Save new exam date
    Given 1b. Teacher, without any previous activity, clicks the button Save new exam date
    Then Teacher is still on the page New Exam Dates
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed
    And Entry form has predefined values as its entries

  Scenario: UC.14 1c. Teacher intends to select a subject that already has all 3 exam dates announced. These subjects are not listed in the dropdown menu
    Given 1c. Teacher intends to select a subject that already has all 3 exam dates announced. These subjects are not listed in the dropdown menu
    When 1c-1. The UC.14 cannot proceed
    Then N/A

  Scenario: UC.14 2a. Teacher sets a maximum of participants as less than 1
    Given 2a. Teacher sets a maximum of participants as less than 1
    When 2a-1. Teacher enters the exam date according the formula from place holder
    When 2a-2. Teacher clicks on the button Save new exam date
    Then Teacher is still on the page New Exam Dates
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed
    And Entry form has predefined values as its entries

  Scenario: UC.14 2b. Teacher sets a maximum of participants as more than 10
    Given 2b. Teacher sets a maximum of participants as more than 10
    When 2b-1. Teacher enters the exam date according the formula from place holder
    When 2b-2. Teacher clicks on the button Save new exam date
    Then Teacher is still on the page New Exam Dates
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed
    And Entry form has predefined values as its entries

  Scenario: UC.14 3a. Teacher sets the first exam date as a date that has already passed
    Given 3a. Teacher sets the first exam date as a date that has already passed
    When 3a-1. Teacher clicks on the button Save new exam date
    Then Teacher is still on the page New Exam Dates
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed
    And Entry form has predefined values as its entries

  Scenario: UC.14 3b. Teacher announces an exam date that is to take place in less than 24 hours after previous one
    Given 3b. Teacher announces an exam date that is to take place in less than 24 hours after previous one
    When 3b-1. Teacher clicks on the button Save new exam date
    Then Teacher is still on the page New Exam Dates
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed
    And Entry form has predefined values as its entries

  Scenario: UC.14 3c. Teacher enters the date in incorrect format
    Given 3c. Teacher enters the date in incorrect format
    When 3c-1. Teacher clicks on the button Save new exam date
    Then Teacher is still on the page New Exam Dates
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed
    And Entry form has predefined values as its entries

  Scenario: UC.14 5a. Internal error occurs in the UIS/DB during the announcement of the subject's exam date in the DB
    Given 5a. Internal error occurs in the UIS/DB during the announcement of the subject's exam date in the DB
    Then Teacher is still on the page New Exam Dates
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.15 Enters the examination evaluation
    Given Teacher is already logged in to the UIS
    And Teacher is on the page Set Evaluation
    When Teacher enters values and entries to the form
    And Teacher selects the desired subject and exam date from the menu
    And Teacher selects the desired student from the dropdown menu
    And Teacher selects the desired evaluation from the dropdown menu
    And Teacher clicks on the button Save evaluation
    And UIS will enter the student's result for the selected subject
    And Message confirming a successful execution will appear
    Then UIS adds the results to the student for the selected subject and edits its DB and its tables accordingly
    And Teacher is still on page Set Evaluation
    And Message confirming a successful execution appears
    And Appropriate subject and the exam date remain selected in the dropdown menu
    And The student disappears from the list in the dropdown menu
    And Evaluation A is predefined in the dropdown menu
    And If the student scored A-E (i.e. he/she passed), he/she is removed from the list in the menu My Subjects
    And If the student scored F (i.e. he/she did not pass), he/she remains on the list in the menu My Subjects
    And The student disappears from the list of examination participans in the menu My Exam Dates
    And The evaluation will appear by the student in the menu Evaluation Table with the filter Includes students with already set grade turned on
    And Student's View: regardless on the evaluation, the subject disappears from the table in the menu My Exam Dates
    And Student's View: if the student scored A-E (i.e. he/she passed), the subject is removed from the table Enrolled Subjects in he menu My Subjects
    And Student's View: if the student scored A-E (i.e. he/she passed), credits are added to the amount in the header of the table Completed Subjects in the menu My Subjects
    And Student's View: if the student scored A-E (i.e. he/she passed), the subject appears with the achieved score in the table Completed Subjects in the menu My Subjects
    And Student's View: if the student scored A-E (i.e. he/she passed), the subject disappears from the table in the menu Other Exam Dates
    And Student's View: if the student scored F (i.e. he/she did not pass), the subject remains in the table Enrolled Subjects in the menu My Subjects
    And Student's View: if the student scored F (i.e. he/she did not pass), the subject remains in the table in the menu Other Exam Dates

  Scenario: UC.15 1a. No entry form is displayed and instead there is a message reading: Warning! No exam dates, i.e. teacher does not have any announced exam dates at the moment
    Given 1a. No entry form is displayed and instead there is a message reading: Warning! No exam dates, i.e. teacher does not have any announced exam dates at the moment
    When 1a-1. UC.15 cannot proceed
    Then N/A

  Scenario: UC.15 1b. Teacher chooses an exam date without any students registered
    Given 1b. Teacher chooses an exam date without any students registered
    Then Teacher is still on page Set Evaluation
    And Entry form displays: No student is registered on this exam date!
    And The button Save evaluation is disabled

  Scenario: UC.15 4a. If the evaluated student is the last student registered on this exam date
    Given 4a. If the evaluated student is the last student registered on this exam date
    Then Conditions 1-4 and 6-16 of the main postcondition list are now enforced
    And Entry form displays: No student is registered on this exam date!
    And Button Save evaluation is disabled

  Scenario: UC.16 Enters or reenters (changes) the evaluation of the examination
    Given Teacher is already logged in to the UIS
    And Teacher is on the page Evaluation Table
    When Teacher enters values and entries to the entry form of the filter
    And Teacher chooses a subject from the dropdown menu of entry form Filter
    And If teacher wants only to enter new evaluations, he/she will keep the checkbox Includes students with already set grade unchecked
    And If teacher wants to search or change already entered evaluations, he/she will check the checkbox Includes students with already set grade.
    And Teacher clicks on the button Filter
    And Teacher chooses the desired evaluation of the student for a specific exam date from the dropdown menu
    And Teacher clicks on the button Submit
    And UIS enters the student's examination result for the selected subject
    And Message confirming a successful execution will appear
    Then UIS enters the subject's evaluation to the student and changes the DB and its tables accordingly
    And Teacher is still on the page Evaluation Table
    And Message confirming a successful execution appears
    And The subject and its exam dates remain visible in the table Evaluation table
    And If the checkbox Includes students with already set grade is checked, the student and his/her evaluation remain visible in the table
    And If the checkbox Includes students with already set grade is not checked, the student is removed from the table
    And If the student scored A-E (i.e. he/she passed), he/she is removed from the list in the menu My Subjects
    And If the student scored F (i.e. he/she did not pass), he/she remains on the list in the menu My Subjects
    And Student is removed from the list of examination participans in the menu My Exam Dates
    And Student is removed from the list of examination participans in the menu Set Evaluation
    And Student's View: regardless of the evaluation the subject disappears from the table in the menu My Exam Dates
    And Student's View: if the student scored A-E (i.e. he/she passed), the subject is removed from the table Enrolled Subjects in the menu My Subjects
    And Student's View: if the student scored A-E (i.e. he/she passed), the credits are added to the amount in the header of the table Completed Subjects in the menu My Subjects
    And Student's View: if the student scored A-E (i.e. he/she passed), the subject appears with the achieved score in the table Completed Subjects in the menu My Subjects
    And Student's View: if the student scored A-E (i.e. he/she passed), the subject disappears from the table in the menu Other Exam Dates
    And Student's View: if the student scored F (i.e. he/she did not pass), the subject remains in the table Enrolled Subjects in the menu My Subjects
    And Student's View: if the student scored F (i.e. he/she did not pass), the subject remains in the table in the menu Other Exam Dates

  Scenario: UC.16 1a. Dropdown menu in the entry form Filter does not show any subject, i.e. Teacher does not teach any subject at the moment
    Given 1a. Dropdown menu in the entry form Filter does not show any subject, i.e. Teacher does not teach any subject at the moment
    When 1a-1. The UC.16 cannot proceed
    Then N/A

  Scenario: UC.16 5a. If there is no exam date for the selected subject and the table Evaluation Table displays: No exam dates for this subject
    Given 5a. If there is no exam date for the selected subject and the table Evaluation Table displays: No exam dates for this subject
    When 5a-1. The UC.16 cannot proceed
    Then N/A

  Scenario: UC.16 6a. If the evaluated student is the last student registered on this term and the checkbox Includes students with already set grade. is unchecked
    Given 6a. If the evaluated student is the last student registered on this term and the checkbox Includes students with already set grade. is unchecked
    Then Conditions 1-17 of the main postcondition list are now enforced
    And Selected term in the table Evaluation table in the menu Evaluation table displays: No students on this exam date

  Scenario: UC.17 Signs up to teach a subject
    Given Teacher is already logged in to the UIS
    And Teacher is on the page Others' Subjects
    When Teacher clicks on the button Participate in the row of the desired subject
    And Teacher clicks on the button Participate in the row of the desired subject
    And UIS will add the subject to the teacher's list of subjects
    And Message confirming a successful execution will appear
    Then UIS adds the subject to the teacher's list of subjects and changes the DB and its tables accordingly
    And Teacher is still on the page Others' Subjects
    And Message confirming a successful execution appears
    And The subject disappears from the list in the menu Others' Subjects
    And The subject appears in the table in the menu My Exam Dates and its' sub-table is empty (i.e. is without exam date)
    And The subject appears on the list in the menu New Exam Dates
    And The subject appears on the list in the menu Evaluation Table
    And The subject appears under this teacher on the list in the menu List of All Teachers
    And Student's View: to every student the teacher appears on the list of teachers leading the subject's sessions in the menu Other Subjects

  Scenario: UC.17 1a. Table has no entries, i.e. the teacher already leads sessions (or is taking a part in the sessions) of all existing subjects
    Given 1a. Table has no entries, i.e. the teacher already leads sessions (or is taking a part in the sessions) of all existing subjects
    When 1a-1. The UC.17 cannot proceed
    Then N/A

  Scenario: UC.17 1b. Teacher intends to teach subject that is already taught by two other teachers
    Given 1b. Teacher intends to teach subject that is already taught by two other teachers
    When 1b-1. The UC.17 cannot proceed
    Then N/A

  Scenario: UC.17 2a. Internal error occurs in the UIS/DB during the uploading of the information in the DB
    Given 2a. Internal error occurs in the UIS/DB during the uploading of the information in the DB
    Then Teacher is still on the page Others' Subjects
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.18 Displays the list of teachers and subjects they teach
    Given Teacher is already logged in to the UIS
    When Teacher clicks on the option List of All Teachers of the menu
    And Teacher clicks on the option of the menu List of All Teachers
    Then Table List of All Teachers is displayed
    And No data are overwritten or saved - no changes occur

  Scenario: UC.18 1a. There is no subject in the UIS
    Given 1a. There is no subject in the UIS
    Then Column of subjects is empty

  Scenario: UC.19 Restoration of the database
    Given No one is logged in the UIS - the upper menu contains the option Restore DB
    When Unlogged user clicks on the option Restore DB of the menu
    And Unlogged user clicks on the option Restore DB of the menu
    And Message confirming a successful execution will appear
    Then User is on the page University information System (Home page)
    And Message confirming a successful execution appears

  Scenario: UC.20 Displays information about system's abilities
    Given No one is logged in to the UIS
    And User is on the page University information System (Home page)
    When Unlogged user clicks on one of the options on the list on the lower left part of the UI/display
    And Unlogged user clicks on one of the following options: Application use-cases, Database content, Application constraints
    And Desired information will display
    Then Desired information is displayed

  Scenario: UC.21 Export of the database
    Given >No one is logged in to the UIS - the upper menu has the option Export/Import DB
    When Unlogged user clicks on the Export/Import DB item on the menu
    And Unlogged user clicks on the Export/Import DB item on the menu
    And Unlogged user chooses either a XML or a JSON file in the Export DB to file form
    And Unlogged user clicks on the button Export
    And Message of a web browser will appear with input for specifying the location of the file
    And Web browser will save the file with a predefined name (e.g. `2019-12-02_18-11_DB-export.xml`) to the desired directory
    Then User is still on the page Export/Import DB

  Scenario: UC.22 Import of the database
    Given No one is logged in to the UIS - the upper menu has the option Export/Import DB
    When Unlogged user clicks on the Export/Import DB item on the menu
    And Unlogged user clicks on the Export/Import DB item on the menu
    And Unlogged user clicks on the Browse (or its bilingual equivalent) option in the form Import data into DB)
    And Unlogged user chooses the desired XML or JSON file
    And Unlogged user clicks on the button Import
    And Message confirming a successful execution will appear
    Then User is still on the page Export/Import DB
    And Message confirming a successful execution appears

  Scenario: UC.22 1a. Unlogged user clicks on the button Import
    Given 1a. Unlogged user clicks on the button Import
    Then User is still on the page Export/Import DB
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.22 4a. The imported file does not have a correct format or content
    Given 4a. The imported file does not have a correct format or content
    Then User is still on the page Export/Import DB
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed

  Scenario: UC.22 4b. Internal error occurs in the UIS/DB during the setting of the new DB content
    Given 4b. Internal error occurs in the UIS/DB during the setting of the new DB content
    Then User is still on the page Export/Import DB
    And Message claiming an unsuccessful execution appears
    And No data are overwritten or changed
