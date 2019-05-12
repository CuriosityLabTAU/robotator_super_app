#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import copy

the_path = 'lecture_files/'
the_file = '6fe89170-73dd-11e9-a32f-5b02d2874b9e.json'
lecture = json.load(open(the_path + the_file))
# convert lecture json to activity json


def print_part(part_):
    for k in ['tag', 'action', 'next']:
        print(k, ':', part_[k])
    if 'end' in part_:
        print(part_['end'])
    print


def generate_text_for_speech(lecture_):
    for s, section_ in enumerate(lecture['sections']):
        if section_['notes']:
            f = open('speech_files/section_%s.txt' % section_['name'], 'w+')
            f.write(section_['notes'])
            f.close()

generate_text_for_speech(lecture)

# TODO: go over sections, and create the json flow
base_robot_action = {
    'tag': 'tag',
    'target': 'robot',
    'action': 'play_audio_file',
    'parameters': 'parameters',
    'next': 'next',
    'debug': 'debug'
}

base_robot_sleep = {
    'tag': 'tag',
    'target': 'robot',
    'action': 'sleep',
    'seconds': 90,
    'done': {
        'timeout': 'timeout',
        'done': 'done'
    },
    'next': 'next',
    'debug': 'debug'
}

base_robot_resolution = {
    'tag': 'tag',
    'target': 'robot',
    'action': 'resolution',
    'seconds': 60,
    'done': {
        'timeout': 'timeout',
        'done': 'done'
    },
    'next': 'next',
    'debug': 'debug'
}

base_tablet_action = {
    'tag': 'tag',
    'target': 'tablet',
    'action': 'show_screen',
    'screen_name': 'screen_name',
    'activity': 'activity',
    'activity_type': 'activity_type',
    'duration': 0,
    'response': 0,
    'tablets': [1,2,3,4,5],
    'next': 'next'
}

# study_flow

study_flow = [{
      "tag": "start", "target": "robot",
      "action":"wake_up",
      "next": 'section_%s_show_screen' % lecture['sections'][1]['name']
    }
]
print(lecture)
for s, section in enumerate(lecture['sections']):
    if s == 0:
        continue
    # Every section is composed of:
    # - a new tablet screen
    # - robot says something
    # - some kind of interaction with the tablet
    # - *task dependent* reaction from the robot
    value = json.loads(section['value'])
    parts = []

    # show screen is always
    part = copy.copy(base_tablet_action)
    part['tag'] = 'section_%s_show_screen' % section['name']
    part['screen_name'] = section['uuid']
    if 'questionType' in value:
        part['activity_type'] = value['questionType']
        part['duration'] = 0 # TODO
        part['response'] = 0 # TODO

    # robot speech is only if there are notes
    if section['notes']:
        if len(section['notes']) > 5:
            part['next'] = 'section_%s_robot_instruction' % section['name']
            parts.append(copy.copy(part))

            part = copy.copy(base_robot_action)
            part['tag'] = parts[-1]['next']
            part['parameters'] = ['section_%s' % section['name']]
    if s < len(lecture['sections']) - 1:
        the_next_part = 'section_%s_show_screen' % lecture['sections'][s + 1]['name']
    else:
        the_next_part = 'lecture_%s' % lecture['name']

    if section['key'] not in ['image']:
        part['next'] = 'section_%s_robot_sleep' % section['name']
        parts.append(copy.copy(part))

        part = copy.copy(base_robot_sleep)
        part['tag'] = parts[-1]['next']
        if 'timeLimit' in value:
            if int(value['timeLimit']) < 30: # too short for a reminder
                part['seconds'] = int(value['timeLimit'])
                part['end'] = {
                    'timeout': 'section_%s_robot_resolution' % section['name'],
                    'done': 'section_%s_robot_resolution' % section['name']
                }
                part['next'] = part['tag']
                parts.append(copy.copy(part))
            else:
                # introduce a reminder
                part['seconds'] = int(value['timeLimit']) - 30
                part['end'] = {
                    'timeout': 'robot_30sec_%s' % part['tag'],
                    'done': 'section_%s_robot_resolution' % section['name']
                }
                part['next'] = part['tag']
                parts.append(copy.copy(part))

                # reminder
                part = copy.copy(base_robot_action)
                part['tag'] = parts[-1]['end']['timeout']
                part['parameters'] = ['30_seconds_left']
                part['next'] = 'section_%s_robot_sleep_30' % section['name']
                parts.append(copy.copy(part))

                # final 30 seconds
                part = copy.copy(base_robot_sleep)
                part['tag'] = 'section_%s_robot_sleep_30' % section['name']
                part['seconds'] = 30
                part['end'] = {
                    'timeout': 'section_%s_robot_resolution' % section['name'],
                    'done': 'section_%s_robot_resolution' % section['name']
                }
                part['next'] = 'section_%s_robot_resolution' % section['name']
                parts.append(copy.copy(part))
        else:
            part['second'] = -1 # TODO: check

        # robot resolution (given answers and speakers)
        part = copy.copy(base_robot_resolution)
        part['tag'] = 'section_%s_robot_resolution' % section['name']
        part['end'] = {
            'timeout': the_next_part,
            'done': the_next_part
        }
    part['next'] = the_next_part
    parts.append(copy.copy(part))

    for p in parts:
        print_part(p)
        study_flow.append(p)

    json.dump(study_flow, open('flow_files/%s.json' % lecture['name'], 'w+'))
