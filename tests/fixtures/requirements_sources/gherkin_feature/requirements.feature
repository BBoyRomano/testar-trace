Feature: TbUIS authentication and profile management

  Scenario: Application login
    Given the user is on the UIS homepage
    When the user selects the Login option from the menu located on the right side of the upper bar
    And the user enters pass in the password field
    Then the Overview page appears
    And the Logout option appears in the upper bar on the right

  Scenario: Change of user's personal data
    Given the user is already logged in to the UIS
    And the user is located on the Overview page
    When the user changes data in the First name entry
    And the user presses the Update button
    Then the user is still on the Overview page
    And a message confirming successful execution appears
