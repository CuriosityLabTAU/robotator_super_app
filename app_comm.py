# importing the requests library
import requests

lectures = requests.get('http://localhost/apilocaladmin/api/v1/admin/lectures').json()

print(lectures)

r = requests.post('http://localhost/apilocaladmin/api/v1/admin/lectureSwitchSection', data={
    'lectureUUID': '84926a80-75b1-11e9-8a95-d9cf49bbf65c',
    'sectionUUID': 'd2108530-75b1-11e9-8a95-d9cf49bbf65c'
})
print(r.text)
#
# # api-endpoint
# URL = "http://18.222.211.1/lectureadmin/superadmin"
#
# # location given here
# location = "delhi technological university"
#
# # defining a params dict for the parameters to be sent to the API
# PARAMS = {'address': location}
#
# from requests.auth import HTTPBasicAuth
# r = requests.get(URL, auth=HTTPBasicAuth('super@admin.com', 'secret'))
#
# # # sending get request and saving the response as response object
# # r = requests.get(url=URL)
#
# # extracting data in json format
# # data = r.json()
# print(r)


# #!/usr/bin/env python3
#
# import socket
#
# HOST = '18.222.211.1'  # The server's hostname or IP address
# PORT = 8003        # The port used by the server
#
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     s.connect((HOST, PORT))
#     s.sendall(b'Hello, world')
#     data = s.recv(1024)
#
# print('Received', repr(data))