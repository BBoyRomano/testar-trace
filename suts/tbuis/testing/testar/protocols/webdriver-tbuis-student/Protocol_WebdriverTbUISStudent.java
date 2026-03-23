import java.util.HashSet;
import java.util.Set;

import org.testar.SutVisualization;
import org.testar.managers.InputDataManager;
import org.testar.monkey.RuntimeControlsProtocol;
import org.testar.monkey.alayer.Action;
import org.testar.monkey.alayer.SUT;
import org.testar.monkey.alayer.State;
import org.testar.monkey.alayer.Widget;
import org.testar.monkey.alayer.actions.AnnotatingActionCompiler;
import org.testar.monkey.alayer.actions.StdActionCompiler;
import org.testar.monkey.alayer.exceptions.ActionBuildException;
import org.testar.monkey.alayer.webdriver.enums.WdTags;
import org.testar.protocols.WebdriverProtocol;

import static org.testar.monkey.alayer.Tags.Blocked;
import static org.testar.monkey.alayer.Tags.Enabled;

public class Protocol_webdriver_tbuis_student extends WebdriverProtocol {

    private static final String USERNAME = "blue";
    private static final String PASSWORD = "pass";

    private static final String TAG_NAME = "id";
    private static final String USERNAME_FIELD_ID = "loginPage.userNameInput";
    private static final String PASSWORD_FIELD_ID = "loginPage.passwordInput";
    private static final String LOGIN_BUTTON_ID = "loginPage.loginFormSubmit";

    private static final int LOGIN_WAIT_SECONDS = 5;
    private static final double LOGIN_RETRY_INTERVAL_SECONDS = 1.0;

    @Override
    protected void beginSequence(SUT system, State state) {
        super.beginSequence(system, state);
        performLogin(system, state, USERNAME, PASSWORD);
    }

    @Override
    protected Set<Action> deriveActions(SUT system, State state) throws ActionBuildException {
        Set<Action> actions = super.deriveActions(system, state);
        Set<Action> filteredActions = new HashSet<>();

        StdActionCompiler actionCompiler = new AnnotatingActionCompiler();
        Set<Action> forcedActions = detectForcedActions(state, actionCompiler);

        for (Widget widget : state) {
            if (!isEnabled(widget)) {
                continue;
            }

            if (isBlackListed(widget)) {
                addBlackListedAction(filteredActions, actionCompiler, widget);
                continue;
            }

            addSlidingActions(actions, actionCompiler, widget);

            if (isBlockedNonShadow(widget)) {
                continue;
            }

            addTypingAction(actions, filteredActions, actionCompiler, widget);
            addClickAction(actions, filteredActions, actionCompiler, widget);
        }

        if (forcedActions != null && !forcedActions.isEmpty()) {
            filteredActions = actions;
            actions = forcedActions;
        }

        if (visualizationOn || mode() == RuntimeControlsProtocol.Modes.Spy) {
            SutVisualization.visualizeFilteredActions(cv, state, filteredActions);
        }

        return actions;
    }

    private void performLogin(SUT system, State state, String username, String password) {
        waitLeftClickAndTypeIntoWidgetWithMatchingTag(
                TAG_NAME,
                USERNAME_FIELD_ID,
                username,
                state,
                system,
                LOGIN_WAIT_SECONDS,
                LOGIN_RETRY_INTERVAL_SECONDS
        );

        waitLeftClickAndTypeIntoWidgetWithMatchingTag(
                TAG_NAME,
                PASSWORD_FIELD_ID,
                password,
                state,
                system,
                LOGIN_WAIT_SECONDS,
                LOGIN_RETRY_INTERVAL_SECONDS
        );

        waitAndLeftClickWidgetWithMatchingTag(
                TAG_NAME,
                LOGIN_BUTTON_ID,
                state,
                system,
                LOGIN_WAIT_SECONDS,
                LOGIN_RETRY_INTERVAL_SECONDS
        );
    }

    private boolean isEnabled(Widget widget) {
        return widget.get(Enabled, true);
    }

    private boolean isBlackListed(Widget widget) {
        return blackListed(widget);
    }

    private boolean isBlockedNonShadow(Widget widget) {
        return widget.get(Blocked, false) && !widget.get(WdTags.WebIsShadow, false);
    }

    private boolean isAllowedActionWidget(Widget widget) {
        return whiteListed(widget) || isUnfiltered(widget);
    }

    private void addBlackListedAction(Set<Action> filteredActions, StdActionCompiler actionCompiler, Widget widget)
            throws ActionBuildException {
        if (isTypeable(widget)) {
            filteredActions.add(createTypeAction(actionCompiler, widget));
            return;
        }

        filteredActions.add(actionCompiler.leftClickAt(widget));
    }

    private void addTypingAction(
            Set<Action> actions,
            Set<Action> filteredActions,
            StdActionCompiler actionCompiler,
            Widget widget) throws ActionBuildException {

        if (!isAtBrowserCanvas(widget) || !isTypeable(widget)) {
            return;
        }

        Action typeAction = createTypeAction(actionCompiler, widget);

        if (isAllowedActionWidget(widget)) {
            actions.add(typeAction);
            return;
        }

        filteredActions.add(typeAction);
    }

    private void addClickAction(
            Set<Action> actions,
            Set<Action> filteredActions,
            StdActionCompiler actionCompiler,
            Widget widget) throws ActionBuildException {

        if (!isAtBrowserCanvas(widget) || !isClickable(widget)) {
            return;
        }

        Action clickAction = actionCompiler.leftClickAt(widget);

        if (!isAllowedActionWidget(widget)) {
            filteredActions.add(clickAction);
            return;
        }

        if (isLinkDenied(widget)) {
            filteredActions.add(clickAction);
            return;
        }

        actions.add(clickAction);
    }

    private Action createTypeAction(StdActionCompiler actionCompiler, Widget widget) throws ActionBuildException {
        return actionCompiler.clickTypeInto(
                widget,
                InputDataManager.getRandomTextInputData(widget),
                true
        );
    }
}
