import java.util.Collections;

import org.testar.monkey.alayer.Action;
import org.testar.monkey.alayer.SUT;
import org.testar.monkey.alayer.State;
import org.testar.protocols.WebdriverProtocol;

public class Protocol_tbuis_uc05 extends WebdriverProtocol {

    private boolean recordActions;

    @Override
    protected void beginSequence(SUT system, State state) {
        super.beginSequence(system, state);

        recordActions = false;
        restoreDatabase(system);

        switch (sequenceCount()) {
            case 1:
                prepareCompletedSubject(system);
                login(system, "blue", "pass");

                recordActions = true;
                openMySubjects(system);
                break;
            case 2:
                login(system, "blue", "pass");

                recordActions = true;
                openMySubjects(system);
                break;
            default:
                throw new IllegalStateException("No UC.05 flow configured for sequence " + sequenceCount());
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

    private void prepareCompletedSubject(SUT system) {
        login(system, "blue", "pass");

        waitAndLeftClickWidgetWithMatchingTag("id", "stu.menu.otherExamDates", getState(system), system, 10, 0.5);
        waitAndLeftClickWidgetWithMatchingTag("id", "stu.otherExamDates.table.registerButton-0-0", getState(system), system, 10, 0.5);

        logout(system);

        login(system, "scatterbrained", "pass");

        waitAndLeftClickWidgetWithMatchingTag("id", "tea.menu.setEvaluation", getState(system), system, 10, 0.5);
        waitAndLeftClickWidgetWithMatchingTag("id", "tea.setEvaluation.form.saveButton", getState(system), system, 10, 0.5);

        logout(system);
    }

    private void login(SUT system, String username, String password) {
        waitAndLeftClickWidgetWithMatchingTag("id", "header.link.login", getState(system), system, 10, 0.5);
        waitLeftClickAndTypeIntoWidgetWithMatchingTag("id", "loginPage.userNameInput", username, getState(system), system, 10, 0.5);
        waitLeftClickAndTypeIntoWidgetWithMatchingTag("id", "loginPage.passwordInput", password, getState(system), system, 10, 0.5);
        waitAndLeftClickWidgetWithMatchingTag("id", "loginPage.loginFormSubmit", getState(system), system, 10, 0.5);
    }

    private void logout(SUT system) {
        waitAndLeftClickWidgetWithMatchingTag("id", "header.link.logout", getState(system), system, 10, 0.5);
    }

    private void openMySubjects(SUT system) {
        waitAndLeftClickWidgetWithMatchingTag("id", "stu.menu.mySubjects", getState(system), system, 10, 0.5);
    }

    private void restoreDatabase(SUT system) {
        waitAndLeftClickWidgetWithMatchingTag("id", "header.link.restoreDB", getState(system), system, 10, 0.5);
    }
}
