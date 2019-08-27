import os
import requests

# delete all lectures
prior_lectures = requests.get('http://localhost/apilocaladmin/api/v1/admin/lectures').json()

for lecture in prior_lectures:
    requests.delete('http://localhost/apilocaladmin/api/v1/admin/lectures/%s/delete' % lecture['uuid'])

# get lectures on file
lecture_path = 'lecture_files'
lecture_files = [lecture_path + '/' + filename for filename in os.listdir(lecture_path) if '.zip' in filename]
print(lecture_files)

# import lectures
for lecture in lecture_files:
    json_files = lecture[:-4]
    full_json_filename
    full_lecture_filename = os.getcwd() + '/' + lecture
    print(full_lecture_filename)
    r = requests.post('http://localhost/apilocaladmin/api/v1/admin/lectures',
                      data={'title': full_lecture_filename, '': full_lecture_filename})
    print(r, r.text)