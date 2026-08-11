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
