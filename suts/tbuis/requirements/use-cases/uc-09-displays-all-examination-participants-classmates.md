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
