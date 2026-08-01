import java.util.Collections;

import org.testar.monkey.alayer.Action;
import org.testar.monkey.alayer.SUT;
import org.testar.monkey.alayer.State;
import org.testar.protocols.WebdriverProtocol;

public class Protocol_tbuis_uc03 extends WebdriverProtocol {

    private boolean recordActions;

    @Override
    protected void beginSequence(SUT system, State state) {
        super.beginSequence(system, state);

        recordActions = false;
        restoreDatabase(system);

        switch (sequenceCount()) {
            case 1:
                updateField(system, "blue", "overview.firstName", "A");
                break;
            case 2:
                updateField(system, "blue", "overview.firstName", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA");
                break;
            case 3:
                updateField(system, "blue", "overview.lastName", "B");
                break;
            case 4:
                updateField(system, "blue", "overview.lastName", "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB");
                break;
            case 5:
                updateField(system, "blue", "overview.email", "a@b.co");
                break;
            case 6:
                updateField(system, "blue", "overview.email", "abcdefghijklmnopqrstuvwxyz1234567890@example.com");
                break;
            case 7:
                updateField(system, "Easyrider", "overview.firstName", "A");
                break;
            case 8:
                updateField(system, "Easyrider", "overview.firstName", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA");
                break;
            case 9:
                updateField(system, "Easyrider", "overview.lastName", "B");
                break;
            case 10:
                updateField(system, "Easyrider", "overview.lastName", "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB");
                break;
            case 11:
                updateField(system, "Easyrider", "overview.email", "a@b.co");
                break;
            case 12:
                updateField(system, "Easyrider", "overview.email", "abcdefghijklmnopqrstuvwxyz1234567890@example.com");
                break;
            case 13:
                updateProfile(system, "blue", "Student", "Updated", "student.updated@example.com");
                break;
            case 14:
                updateProfile(system, "Easyrider", "Teacher", "Updated", "teacher.updated@example.com");
                break;
            default:
                throw new IllegalStateException("No UC.03 flow configured for sequence " + sequenceCount());
        }
    }

    @Override
    protected boolean executeTriggeredAction(SUT system, State state, Action action) {
        if (recordActions) {
            stateModelManager.notifyNewStateReached(state, Collections.singleton(action));
        }

        boolean executed = super.executeTriggeredAction(system, state, action);

        if (recordActions) {
            stateModelManager.notifyActionExecution(action);
        }

        return executed;
    }

    private void updateField(SUT system, String username, String fieldId, String value) {
        login(system, username, "pass");

        recordActions = true;

        waitLeftClickAndTypeIntoWidgetWithMatchingTag("id", fieldId, value, getState(system), system, 10, 0.5);
        waitAndLeftClickWidgetWithMatchingTag("id", "overview.saveButton", getState(system), system, 10, 0.5);
    }

    private void updateProfile(SUT system, String username, String firstName, String lastName, String email) {
        login(system, username, "pass");

        recordActions = true;

        waitLeftClickAndTypeIntoWidgetWithMatchingTag("id", "overview.firstName", firstName, getState(system), system, 10, 0.5);
        waitLeftClickAndTypeIntoWidgetWithMatchingTag("id", "overview.lastName", lastName, getState(system), system, 10, 0.5);
        waitLeftClickAndTypeIntoWidgetWithMatchingTag("id", "overview.email", email, getState(system), system, 10, 0.5);
        waitAndLeftClickWidgetWithMatchingTag("id", "overview.saveButton", getState(system), system, 10, 0.5);
    }

    private void login(SUT system, String username, String password) {
        waitAndLeftClickWidgetWithMatchingTag("id", "header.link.login", getState(system), system, 10, 0.5);
        waitLeftClickAndTypeIntoWidgetWithMatchingTag("id", "loginPage.userNameInput", username, getState(system), system, 10, 0.5);
        waitLeftClickAndTypeIntoWidgetWithMatchingTag("id", "loginPage.passwordInput", password, getState(system), system, 10, 0.5);
        waitAndLeftClickWidgetWithMatchingTag("id", "loginPage.loginFormSubmit", getState(system), system, 10, 0.5);
    }

    private void restoreDatabase(SUT system) {
        waitAndLeftClickWidgetWithMatchingTag("id", "header.link.restoreDB", getState(system), system, 10, 0.5);
    }
}
