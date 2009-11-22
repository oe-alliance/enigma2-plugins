from Components.ActionMap import NumberActionMap, HelpableActionMap

class HelpableNumberActionMap(HelpableActionMap, NumberActionMap):
    """This Actionmap is a HelpableActionMap and a NumberActionMap at the same time.
    It does not have any code, just inherits the init-method from HelpableActionMap and the action from the NumberActionMap"""
    def action(self, contexts, action):
        NumberActionMap.action(self, contexts, action)
    def __init__(self, parent, context, actions = { }, prio=0):
        HelpableActionMap.__init__(self, parent, context, actions, prio)