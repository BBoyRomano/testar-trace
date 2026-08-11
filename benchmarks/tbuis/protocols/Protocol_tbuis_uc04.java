import java.util.Collections;

import org.testar.monkey.alayer.Action;
import org.testar.monkey.alayer.SUT;
import org.testar.monkey.alayer.State;
import org.testar.monkey.alayer.Widget;
import org.testar.monkey.alayer.actions.WdSelectListAction;
import org.testar.monkey.alayer.actions.WdSelectListAction.JsTargetMethod;
import org.testar.monkey.alayer.webdriver.WdDriver;
import org.testar.protocols.WebdriverProtocol;

public class Protocol_tbuis_uc04 extends WebdriverProtocol {

    private boolean recordActions;

    @Override
    protected void beginSequence(SUT system, State state) {
        super.beginSequence(system, state);

        recordActions = false;
        restoreDatabase(system);
        login(system);
        openMySubjects(system);

        recordActions = true;

        switch (sequenceCount()) {
            case 1:
                openUnenrollModal(system);
                waitAndLeftClickWidgetWithMatchingTag("id", "stu.mySubjects.unenrollSubjectModal.CloseModalButton", getState(system), system, 10, 0.5);
                break;
            case 2:
                openUnenrollModal(system);
                selectAnotherSubject(system);
                confirmUnenrollment(system);
                break;
            case 3:
                openUnenrollModal(system);
                confirmUnenrollment(system);
                break;
            case 4:
                recordActions = false;
                unenrollAllSubjects(system);
                waitAndLeftClickWidgetWithMatchingTag("id", "stu.menu.overview", getState(system), system, 10, 0.5);

                recordActions = true;
                openMySubjects(system);
                break;
            default:
                throw new IllegalStateException("No UC.04 flow configured for sequence " + sequenceCount());
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

    private void openUnenrollModal(SUT system) {
        waitAndLeftClickWidgetWithMatchingTag("id", "stu.mySubjects.enrolledTable.unenrollSubjectButton-0", getState(system), system, 10, 0.5);
    }

    private void selectAnotherSubject(SUT system) {
        State state = getState(system);
        Widget select = getWidgetWithMatchingTag("id", "stu.mySubjects.unenrollSubjectModal.subjectSelect", state);

        if (select == null) {
            throw new IllegalStateException("UC.04 subject selector was not found");
        }

        Object value = WdDriver.executeScript(
                "const field = document.getElementById('stu.mySubjects.unenrollSubjectModal.subjectSelect');" +
                "if (!field) return null;" +
                "const option = Array.from(field.options).find(option => !option.selected && !option.disabled && option.value !== '');" +
                "return option ? option.value : null;"
        );

        if (value == null) {
            throw new IllegalStateException("UC.04 alternative flow requires at least two enrolled subjects");
        }

        Action action = new WdSelectListAction(
                "stu.mySubjects.unenrollSubjectModal.subjectSelect",
                value.toString(),
                select,
                JsTargetMethod.ID
        );

        buildStateActionsIdentifiers(state, Collections.singleton(action));
        executeTriggeredAction(system, state, action);
    }

    private void confirmUnenrollment(SUT system) {
        waitAndLeftClickWidgetWithMatchingTag("id", "stu.mySubjects.unenrollSubjectModal.unenrollSubjectButton", getState(system), system, 10, 0.5);
    }

    private void unenrollAllSubjects(SUT system) {
        Object count = WdDriver.executeScript(
                "return document.querySelectorAll('[id^=\"stu.mySubjects.enrolledTable.unenrollSubjectButton-\"]').length;"
        );

        int subjectCount = Integer.parseInt(count.toString());

        for (int i = 0; i < subjectCount; i++) {
            openUnenrollModal(system);
            confirmUnenrollment(system);
        }
    }

    private void login(SUT system) {
        waitAndLeftClickWidgetWithMatchingTag("id", "header.link.login", getState(system), system, 10, 0.5);
        waitLeftClickAndTypeIntoWidgetWithMatchingTag("id", "loginPage.userNameInput", "blue", getState(system), system, 10, 0.5);
        waitLeftClickAndTypeIntoWidgetWithMatchingTag("id", "loginPage.passwordInput", "pass", getState(system), system, 10, 0.5);
        waitAndLeftClickWidgetWithMatchingTag("id", "loginPage.loginFormSubmit", getState(system), system, 10, 0.5);
    }

    private void openMySubjects(SUT system) {
        waitAndLeftClickWidgetWithMatchingTag("id", "stu.menu.mySubjects", getState(system), system, 10, 0.5);
    }

    private void restoreDatabase(SUT system) {
        waitAndLeftClickWidgetWithMatchingTag("id", "header.link.restoreDB", getState(system), system, 10, 0.5);
    }
}
