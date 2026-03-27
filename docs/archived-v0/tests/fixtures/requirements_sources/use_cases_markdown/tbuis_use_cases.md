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
