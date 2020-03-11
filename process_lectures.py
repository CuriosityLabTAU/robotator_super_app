import os
import requests
from read_lecture import *

# delete all lectures
lectures = requests.get('http://localhost:8003/apilocaladmin/api/v1/admin/lectures').json()

# for lecture in prior_lectures:
#     requests.delete('http://localhost/apilocaladmin/api/v1/admin/lectures/%s/delete' % lecture['uuid'])
#
# # get lectures on file
# lecture_path = 'lecture_files'
# lecture_files = [lecture_path + '/' + filename for filename in os.listdir(lecture_path) if '.zip' in filename]
# print(lecture_files)
#
# # import lectures
# for lecture in lecture_files:
#     json_files = lecture[:-4]
#     full_json_filename
#     full_lecture_filename = os.getcwd() + '/' + lecture
#     print(full_lecture_filename)
#     r = requests.post('http://localhost/apilocaladmin/api/v1/admin/lectures',
#                       data={'title': full_lecture_filename, '': full_lecture_filename})
#     print(r, r.text)

for lecture in lectures:
    print(lecture)
    if lecture['name'] == 'test_debate':
        convert_lecture_to_flow_robotod(lecture)

generic_lecture_uuid = u'd9603110-5f25-11ea-9cca-75737e6ac11c'
wait_for_explanation = u'eb14f7b0-5f25-11ea-9cca-75737e6ac11c'