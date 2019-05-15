import os
import requests

# delete all lectures
prior_lectures = requests.get('http://localhost/apilocaladmin/api/v1/admin/lectures').json()

for lecture in prior_lectures:
    requests.delete('http://localhost/apilocaladmin/api/v1/admin/lectures/%s/delete' % lecture['uuid'])

# get lectures on file
lecture_path = 'lecture_files/'
lecture_files = [lecture_path + '/' + filename for filename in os.listdir(lecture_path) if '.zip' in filename]
print(lecture_files)

# import lectures
for lecture in lecture_files:
    full_lecture_filename = '~/PycharmProjects/robotator_super_app/' + lecture
    print(full_lecture_filename)
    r = requests.post('http://localhost/apilocaladmin/api/v1/admin/lectures/import',
                      data={'file': full_lecture_filename})
    print(r, r.text)