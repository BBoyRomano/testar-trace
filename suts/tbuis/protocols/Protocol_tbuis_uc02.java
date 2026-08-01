import java.util.Collections;

import org.testar.monkey.alayer.Action;
import org.testar.monkey.alayer.SUT;
import org.testar.monkey.alayer.State;
import org.testar.protocols.WebdriverProtocol;

public class Protocol_tbuis_uc02 extends WebdriverProtocol {

    private boolean recordActions;

    @Override
    protected void beginSequence(SUT system, State state) {
        super.beginSequence(system, state);

        recordActions = false;
        restoreDatabase(system);

        switch (sequenceCount()) {
            case 1:
                login(system, "blue", "pass");
                break;
            case 2:
                login(system, "Easyrider", "pass");
                break;
            default:
                throw new IllegalStateException("No UC.02 flow configured for sequence " + sequenceCount());
        }

        recordActions = true;
        waitAndLeftClickWidgetWithMatchingTag("id", "header.link.logout", getState(system), system, 10, 0.5);
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
