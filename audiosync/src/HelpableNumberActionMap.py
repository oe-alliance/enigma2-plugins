from Components.ActionMap import HelpableActionMap

class HelpableNumberActionMap(HelpableActionMap):
    """This Actionmap is a HelpableActionMap and a NumberActionMap at the same time.
    It does not have any code, just inherits the init-method from HelpableActionMap and the action from the NumberActionMap"""
    def action(self, contexts, action):
        numbers = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
        if (action in numbers and action in self.actions):
            res = self.actions[action](int(action))
            if res is not None:
                return res
            return 1
        else:
            return HelpableActionMap.action(self, contexts, action)

    def __init__(self, parent, context, actions={ }, prio=0):
        HelpableActionMap.__init__(self, parent, context, actions, prio)
