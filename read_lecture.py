#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import copy
from convert_text_to_speech_hebrew import *
import os
import subprocess
import numpy as np
from mp3_to_amplitude import path_to_lip_csv
from pydub import AudioSegment

base_robot_animated_text = {
    'tag': 'tag',
    'target': 'robot',
    'action': 'run_block',
    'parameters': ['/home/curious/PycharmProjects/run_general_robot_script/shorashim/robotod/blocks/Explain_4.new',
                   '/home/curious/PycharmProjects/run_general_robot_script/shorashim/robotod/sounds/00.mp3'],
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
    'seconds': 15,
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

base_debate = []
base_debate.append(copy.copy(base_tablet_action))
base_debate.append(copy.copy(base_robot_animated_text))
base_debate.append((copy.copy(base_robot_sleep)))




def mp3_file_length(filename):
    args = ("ffprobe", "-show_entries", "format=duration", "-i", filename)
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    output = popen.stdout.read().split('\n')[1].split('=')[1]
    return output


def isEnglish(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


def print_part(part_):
    for k in ['tag', 'action', 'next']:
        print(k, ':', part_[k])
    if 'end' in part_:
        print(part_['end'])
    print


def convert_lecture_to_flow_nao(lecture, the_lecture_hash=None):
    base_robot_action = {
        'tag': 'tag',
        'target': 'robot',
        'action': 'play_audio_file',
        'parameters': 'parameters',
        'next': 'next',
        'debug': 'debug'
    }

    base_robot_animated_text = {
        'tag': 'tag',
        'target': 'robot',
        'action': 'animated_text_to_speech',
        'parameters': ['parameters'],
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
        'seconds': 15,
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
        'tablets': [1, 2, 3, 4, 5],
        'next': 'next'
    }

    the_path = 'lecture_files/'
    # the_lecture_hash = '60aa4b40-765d-11e9-b4b4-cf18aea23797'
    # the_lecture_hash = 'eff1b350-7640-11e9-b4b4-cf18aea23797'
    # the_lecture_hash = 'f6782e00-7660-11e9-b4b4-cf18aea23797'
    # the_lecture_hash = '7ee48240-c8a3-11e9-962c-efd40309cb4c'
    if the_lecture_hash:
        the_file = the_lecture_hash + '/' + the_lecture_hash + '.json'
        lecture = json.load(open(the_path + the_file))
    # convert lecture json to activity json

    def generate_text_for_speech(lecture_):
        for s, section_ in enumerate(lecture['sections']):
            if section_['notes']:
                f = open('speech_files/section_%s.txt' % section_['name'], 'w+')
                f.write(section_['notes'].encode('utf-8'))
                f.close()

    generate_text_for_speech(lecture)

    # go over sections, and create the json flow


    # study_flow
    ordered_sections = []
    for s, section_uuid in enumerate(json.loads(lecture['sectionsOrdering'])):
        section = [sec for sec in lecture['sections'] if sec['uuid'] == section_uuid][0]
        ordered_sections.append(copy.copy(section))


    study_flow = [{
          "tag": "start", "target": "robot",
          "action":"wake_up",
          "next": 'section_%s_show_screen' % ordered_sections[0]['name']
        }
    ]
    print(lecture)
    print(lecture['sectionsOrdering'])
    for s, section in enumerate(ordered_sections):
        print(section['uuid'])
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
            part['duration'] = int(value['timeLimit'])
            part['response'] = 1 # TODO
        elif 'canRespond' in value:
            if value['canRespond']:
                part['response'] = 1
                part['duration'] = int(value['timeLimit'])

        # robot speech is only if there are notes
        if section['notes']:
            if len(section['notes']) > 5:
                part['next'] = 'section_%s_robot_instruction' % section['name']
                parts.append(copy.copy(part))

                if isEnglish(section['notes']):
                    part = copy.copy(base_robot_animated_text)
                    part['parameters'] = [section['notes'].replace('\\wait\\',
                                                                   '^run(animations/Stand/Gestures/Explain_1)')]
                else:
                    part = copy.copy(base_robot_action)
                    part['parameters'] = ['section_%s' % section['name']]
                part['tag'] = parts[-1]['next']

        if s < len(lecture['sections']) - 1:
            the_next_part = 'section_%s_show_screen' % ordered_sections[s + 1]['name']
        else:
            the_next_part = 'end'

        section_value = json.loads(section['value'])
        student_respond = False
        if 'canRespond' in section_value:
            student_respond = section_value['canRespond']
        elif section['key'] in ['quiz', 'imageQuestion']:
            student_respond = True

        if student_respond:
            part['next'] = 'section_%s_robot_sleep' % section['name']
            parts.append(copy.copy(part))

            after_response = 'section_%s_robot_resolution' % section['name']
            if 'text' in section['key']:
                after_response = the_next_part

            part = copy.copy(base_robot_sleep)
            part['tag'] = parts[-1]['next']
            if 'timeLimit' in value:
                if int(value['timeLimit']) <= 30: # too short for a reminder
                    part['seconds'] = int(value['timeLimit'])
                    part['done'] = {
                        'timeout': after_response,
                        'done': after_response
                    }
                    part['next'] = part['tag']
                    parts.append(copy.copy(part))
                else:
                    # introduce a reminder
                    part['seconds'] = int(value['timeLimit']) - 30
                    part['done'] = {
                        'timeout': 'robot_30sec_%s' % part['tag'],
                        'done': after_response
                    }
                    part['next'] = part['tag']
                    parts.append(copy.copy(part))

                    # reminder
                    # English
                    part = copy.copy(base_robot_animated_text)
                    part['parameters'] = ['You have only 30 seconds left.']
                    # # Recordings
                    # part = copy.copy(base_robot_action)
                    # part['parameters'] = ['30_seconds_left']

                    part['tag'] = parts[-1]['done']['timeout']
                    part['next'] = 'section_%s_robot_sleep_30' % section['name']
                    parts.append(copy.copy(part))

                    # final 30 seconds
                    part = copy.copy(base_robot_sleep)
                    part['tag'] = 'section_%s_robot_sleep_30' % section['name']
                    part['seconds'] = 30
                    part['done'] = {
                        'timeout': after_response,
                        'done': after_response
                    }
                    part['next'] = after_response
                    parts.append(copy.copy(part))
            else:
                part['second'] = -1 # TODO: check

            # robot resolution (given answers and speakers)
            part = copy.copy(base_robot_resolution)
            part['tag'] = 'section_%s_robot_resolution' % section['name']
            part['done'] = {
                'timeout': the_next_part,
                'done': the_next_part
            }
        part['next'] = the_next_part
        parts.append(copy.copy(part))

        for p in parts:
            print_part(p)
            study_flow.append(p)

        json.dump(study_flow, open('flow_files/%s.json' % lecture['name'], 'w+'))


def convert_hebrew_to_ascii(s):
    if isEnglish(s):
        return s
    else:
        return s.encode('ascii', 'xmlcharrefreplace')


def generate_text_to_speech(lecture_, the_path):
    for s, section_ in enumerate(lecture_['sections']):
        if section_['notes']:
            if len(section_['notes'].strip()) > 0:
                filename = '%ssection_%s.mp3' % (the_path, section_['name'])
                if not os.path.exists(filename):
                    tts_heb(text=section_['notes'].encode('utf-8'),
                            filename=filename)

        # try:
        #     # TODO CHANGE GOREN
        #     if section_['value']:
        #         value = json.loads(section_['value'])
        #         if value['answers']:
        #             for a in value['answers']:
        #                 if a['truth']:
        #                     filename = '%ssection_%s_correct_temp.mp3' % (the_path, section_['name'])
        #                     if not os.path.exists(filename):
        #                         tts_heb(text=a['text'].encode('utf-8'),
        #                                 filename=filename)
        #
        #                     mp3_after = AudioSegment.from_mp3(filename)
        #                     mp3_before = AudioSegment.from_mp3('robot_files/robotod/blocks/speech_correct.mp3')
        #                     mp3_merge = mp3_before + mp3_after
        #                     mp3_merge.export('%ssection_%s_correct.mp3' % (the_path, section_['name']), format='mp3')
        # except:
        #     print('ERROR in generating correct answer speech')

    print('Adding lip csv ...')
    path_to_lip_csv(the_path)


def convert_lecture_to_flow_robotod(lecture, the_lecture_hash=None):

    the_path = 'lecture_files/' + lecture['name'] + '/'
    # create the path for the lecture files
    if not os.path.exists(the_path):
        os.makedirs(the_path)

    # the_lecture_hash = '60aa4b40-765d-11e9-b4b4-cf18aea23797'
    # the_lecture_hash = 'eff1b350-7640-11e9-b4b4-cf18aea23797'
    # the_lecture_hash = 'f6782e00-7660-11e9-b4b4-cf18aea23797'
    # the_lecture_hash = '7ee48240-c8a3-11e9-962c-efd40309cb4c'
    if the_lecture_hash:
        the_file = the_lecture_hash + '/' + the_lecture_hash + '.json'
        lecture = json.load(open(the_path + the_file))
    # convert lecture json to activity json

    print('Generating text to speech...')
    generate_text_to_speech(lecture, the_path)

    # go over sections, and create the json flow


    # study_flow
    ordered_sections = []
    for s, section_uuid in enumerate(json.loads(lecture['sectionsOrdering'])):
        section = [sec for sec in lecture['sections'] if sec['uuid'] == section_uuid][0]
        ordered_sections.append(copy.copy(section))

    study_flow = [{
          "tag": "start", "target": "robot",
          "action":"wake_up",
          "next": 'init_facilitation'
        },
        {
            "tag": 'init_facilitation', 'target': 'robot',
            'action': 'init_facilitation',
            'next': 'section_%s_show_screen' % ordered_sections[0]['name']
        }
    ]

    part = copy.copy(base_robot_animated_text)
    part['parameters'] = [

    ]

    print(lecture)
    print(lecture['sectionsOrdering'])
    for s, section in enumerate(ordered_sections):
        print(section['uuid'])
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
            if len(value['timeLimit']) == 0:
                print("ERROR", value)
                value['timeLimit'] = 30
            part['duration'] = int(value['timeLimit'])
            part['response'] = 1 # TODO
        elif section['key'] in ['text']:
            part['activity_type'] = 'text'

        if 'canRespond' in value:
            if value['canRespond']:
                part['response'] = 1
                part['duration'] = int(value['timeLimit'])

        # If it's a quiz, save also the answer
        # and prepare a part that says the correct answer
        if section['key'] in ['quiz']:
            part['answers'] = value['answers']

            # says the correct answer
            correct_part = copy.copy(part_animated_speech(the_path, {'name': section['name'] + '_correct'}))
            correct_part['tag'] = part['tag'] + '_correct'
            parts.append(correct_part)



        # robot speech is only if there are notes
        if section['notes']:
            if len(section['notes'].strip()) > 5:
                part['next'] = 'section_%s_robot_instruction' % section['name']
                parts.append(copy.copy(part))

                if isEnglish(section['notes']):
                    part = copy.copy(base_robot_animated_text)
                    ## TODO place here text_to_speech
                    # part['parameters'] = [section['notes'].replace('\\wait\\',
                    #                                                '^run(animations/Stand/Gestures/Explain_1)')]
                else:
                    part = copy.copy(base_robot_animated_text)
                    # find relevant mp3 file
                    # if there is no corresponding block file
                    # -- estimate mp3 length
                    # -- find appropriate block file according to length
                    audio_file = '%ssection_%s.mp3' % (the_path, section['name'])
                    if not os.path.exists(audio_file):
                        print('ERROR: no audio file for the notes. ', audio_file)
                        audio_file = 'example.mp3'
                    block_file = '%ssection_%s.new' % (the_path, section['name'])
                    if not os.path.exists(block_file):
                        # select the behavior to be as long as the sound file
                        # a little shorter, so there won't be movement without sound
                        audio_file_length = np.floor(float(mp3_file_length(audio_file)))
                        closest_block_length = int(audio_file_length / 5.0) * 5
                        if closest_block_length < 0:
                            closest_block_length = 0
                        block_file = 'robot_files/robotod/blocks/explain_%d.new' % closest_block_length
                        if not os.path.exists(block_file):
                            block_file = 'robot_files/robotod/blocks/Explain_4.new'
                        lip_file = 'robot_files/robotod/blocks/explain_%d.csv' % closest_block_length
                    part['parameters'] = [block_file, audio_file, lip_file]
                part['tag'] = parts[-1]['next']

        if s < len(ordered_sections) - 1:
            the_next_part = 'section_%s_show_screen' % ordered_sections[s + 1]['name']
        else:
            the_next_part = 'end'

        section_value = json.loads(section['value'])
        student_respond = False
        if 'canRespond' in section_value:
            student_respond = section_value['canRespond']
        elif section['key'] in ['quiz', 'imageQuestion']:
            student_respond = True

        if student_respond:
            part['next'] = 'section_%s_robot_sleep' % section['name']
            parts.append(copy.copy(part))

            # After response:
            #  if 'text', there there are no right/wrong/same/different answers
            resolution = True
            if 'text' in section['key']:
                resolution = False
            # if dodebate = False, move on
            elif 'doDebate' in value:
                if not value['doDebate']:
                    resolution = False

            if resolution:
                after_response = 'section_%s_robot_resolution' % section['name']
            else:
                after_response = the_next_part

            part = copy.copy(base_robot_sleep)
            part['tag'] = parts[-1]['next']
            if 'timeLimit' in value:
                if int(value['timeLimit']) <= 30: # too short for a reminder
                    part['seconds'] = int(value['timeLimit'])
                    part['done'] = {
                        'timeout': after_response,
                        'done': after_response
                    }
                    part['next'] = part['tag']
                    parts.append(copy.copy(part))
                else:
                    # introduce a reminder
                    part['seconds'] = int(value['timeLimit']) - 30
                    part['done'] = {
                        'timeout': 'robot_30sec_%s' % part['tag'],
                        'done': after_response
                    }
                    part['next'] = part['tag']
                    parts.append(copy.copy(part))

                    # reminder
                    # # English
                    # part = copy.copy(base_robot_animated_text)
                    # part['parameters'] = ['You have only 30 seconds left.']
                    # Recordings
                    part = copy.copy(base_robot_animated_text)
                    part['parameters'] = ['robot_files/robotod/blocks/30_sec_reminder.new', 'robot_files/robotod/blocks/30_sec_reminder.mp3']

                    part['tag'] = parts[-1]['done']['timeout']
                    part['next'] = 'section_%s_robot_sleep_30' % section['name']
                    parts.append(copy.copy(part))

                    # final 30 seconds
                    part = copy.copy(base_robot_sleep)
                    part['tag'] = 'section_%s_robot_sleep_30' % section['name']
                    part['seconds'] = 30
                    part['done'] = {
                        'timeout': after_response,
                        'done': after_response
                    }
                    part['next'] = after_response
                    parts.append(copy.copy(part))
            else:
                part['second'] = -1 # TODO: check

            if resolution:
                # robot resolution (given answers and speakers)
                part = copy.copy(base_robot_resolution)
                part['tag'] = 'section_%s_robot_resolution' % section['name']
                part['done'] = {
                    'timeout': the_next_part,
                    'done': the_next_part
                }


        part['next'] = the_next_part
        parts.append(copy.copy(part))

        for p in parts:
            print_part(p)
            study_flow.append(p)

        json.dump(study_flow, open('flow_files/%s.json' % lecture['name'], 'w+'))

    no_end = True
    for p in study_flow:
        if p['tag'] == 'end':
            no_end = False
    if no_end:
        study_flow.append({
              "tag": "end", "target": "robot",
              "action":"wake_up",
              "next": 'end'
            })
    json.dump(study_flow, open('flow_files/%s.json' % lecture['name'], 'w+'))


def find_appropriate_csv(audio_file):
    # select the behavior to be as long as the sound file
    # a little shorter, so there won't be movement without sound
    audio_file_length = np.floor(float(mp3_file_length(audio_file)))
    closest_block_length = int(audio_file_length / 5.0) * 5
    if closest_block_length < 0:
        closest_block_length = 0
    block_file = 'robot_files/robotod/blocks/explain_%d.new' % closest_block_length
    if not os.path.exists(block_file):
        block_file = 'robot_files/robotod/blocks/Explain_4.new'
    lip_file = 'robot_files/robotod/blocks/explain_%d.csv' % closest_block_length
    return [block_file, audio_file, lip_file]


def part_animated_speech(the_path, section):
    part = copy.copy(base_robot_animated_text)
    # find relevant mp3 file
    # if there is no corresponding block file
    # -- estimate mp3 length
    # -- find appropriate block file according to length
    audio_file = '%ssection_%s.mp3' % (the_path, section['name'])
    if not os.path.exists(audio_file):
        print('ERROR: no audio file for the notes. ', audio_file)
        audio_file = 'example.mp3'
    block_file = '%ssection_%s.new' % (the_path, section['name'])
    if not os.path.exists(block_file):
        # select the behavior to be as long as the sound file
        # a little shorter, so there won't be movement without sound
        audio_file_length = np.floor(float(mp3_file_length(audio_file)))
        closest_block_length = int(audio_file_length / 5.0) * 5
        if closest_block_length < 0:
            closest_block_length = 0
        block_file = 'robot_files/robotod/blocks/explain_%d.new' % closest_block_length
        if not os.path.exists(block_file):
            block_file = 'robot_files/robotod/blocks/Explain_4.new'
        lip_file = 'robot_files/robotod/blocks/explain_%d.csv' % closest_block_length
    part['parameters'] = [block_file, audio_file, lip_file]
    return part
