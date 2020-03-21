import copy
from random import choice

new_user = {
    'engage': [],
    'speak': [],
    'answers': [],
    'correct': [],
    'feedback': {
        'speak': [],
        'correct': []
    }
}

new_behavior = {
    'trigger': None,
    'action': None,
    'priority': 10 # between 0-10
}


class Facilitation:

    def __init__(self):
        self.users = {}
        self.state = {
            'screen': None,
            'answers': {},
            'correct': {},
            'flow': None
        }
        self.action = []
        self.behaviors = [
            {
                'name': 'if all gave correct answers, say correct answer and move on',
                'trigger': 'all|correct|True',
                'action': 'say|correct>next',
                'priority': 10  # between 0-10
            },
            {
                'name': 'if all gave wrong answers, ask someone to explain, say correct answer and move on',
                'trigger': 'all|correct|False',
                'action': 'debate|one|speak|least|explain>say|correct>next',
                'priority': 10  # between 0-10
            },
            {
                'name': 'if some gave wrong answers, ask someone to explain, say correct answer and move on',
                'trigger': 'some|correct|False',
                'action': 'debate|one|speak|least|explain>say|correct>next',
                'priority': 9  # between 0-10
            },
            {
                'name': 'default for no debate',
                'trigger': 'some|correct|False',
                'action': 'say|correct>next',
                'priority': 0  # between 0-10
            },
            {
                'name': 'default for no debate',
                'trigger': 'some|correct|True',
                'action': 'say|correct>next',
                'priority': 1  # between 0-10
            }

        ]

    def add_user(self, subject_id_):
        self.users[subject_id_] = copy.copy(new_user)
        self.state['answers'][subject_id_] = None
        self.state['correct'][subject_id_] = None

    def update_state(self,
                     flow_=None,
                     answer_=None,
                     engage_=None,
                     speak_=None):
        self.action = []

        if flow_:
            self.state['flow'] = flow_
            for u in self.users:
                self.state['correct'][u] = None
                self.state['answers'][u] = None

        if answer_:
            self.users[answer_['subject_id']]['answers'].append(answer_['answer'])
            self.users[answer_['subject_id']]['correct'].append(answer_['correct'])
            self.state['correct'][answer_['subject_id']] = answer_['correct']
            self.state['answers'][answer_['subject_id']] = answer_['answer']
            self.action.extend(self.check_triggers())

        if speak_:
            for s in speak_:
                self.users[s['subject_id']]['speak'] = s['count']

        if engage_:
            pass

        return self.action

    def check_triggers(self):
        actions_ = []
        top_priority = -1
        for b in self.behaviors:
            if self.activate_trigger(b):
                if b['priority'] > top_priority:
                    top_priority = b['priority']
                    actions_ = b['action'].split('>')
                elif b['priority'] == top_priority:
                    actions_.extend(b['action'].split('>'))
        return actions_

    def activate_trigger(self, behavior_):
        active = False
        t = behavior_['trigger'].split('|')
        if 'all' in t:
            # default is activate, only if someone does not meet the condition, change to False
            active = True
            if 'correct' in t:
                if len(self.state['flow']['answers']) > 1:
                    # look in correct
                    for s, c in self.state['correct'].items():
                        if c is None:
                            # missing a user, not all gave answers
                            active = False
                            break
                        if t[-1] == 'True':
                            active = active and c
                        elif t[-1] == 'False':
                            active = active and not c
        elif 'some' in t:
            # default is not to activate, only if someone does not meet the condition, change to False
            active = False
            if 'correct' in t:
                if len(self.state['flow']['answers']) > 1:
                    # look in correct
                    for s, c in self.state['correct'].items():
                        if c is None:
                            # missing a user, not all gave answers
                            active = False
                            break
                        if t[-1] == 'True' and c:
                            active = True
                        elif t[-1] == 'False' and not c:
                            active = True
        return active

    def get_speaker(self, speaker_type):
        speaker_ = None
        if speaker_type =='least':
            count = 1e9
            for u, d in self.users.items():
                if d['speak'] < count:
                    count = d['speak']
                    speaker_ = u
        elif speaker_type == 'most':
            count = -1
            for u, d in self.users.items():
                if d['speak'] > count:
                    count = d['speak']
                    speaker_ = u

        if speaker_ is None:    # no one has been chosen
            # select one at random
            speaker_ = choice(self.users.keys())

        return speaker_



