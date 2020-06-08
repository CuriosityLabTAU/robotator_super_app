is_robot = True
which_robot = 'robotod' # 'nao'
is_sensor = True
is_camera = True
is_generic = True
is_database = True
is_local = True
if is_local:
    ip_coordinator = 'localhost:8003'
else:
    ip_coordinator = '3.14.152.95:8003'
