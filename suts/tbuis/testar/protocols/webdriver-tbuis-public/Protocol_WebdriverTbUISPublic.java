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

public class Protocol_webdriver_tbuis_public extends WebdriverProtocol {

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
