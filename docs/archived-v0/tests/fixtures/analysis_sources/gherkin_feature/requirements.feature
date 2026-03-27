Feature: TbUIS authentication

  Scenario: Application login
    Given the user is on the UIS homepage
    When the user selects the Login option from the menu located on the right side of the upper bar
    And the user presses the Login button
    Then the Overview page appears
    And the Logout option appears in the upper bar on the right
