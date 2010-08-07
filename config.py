from mongrel2.config import *

HOST = '172.16.1.128'

main = Server(
    uuid = "a98eaf71-f06e-4357-bc66-2b7a5a4e072b",
    access_log = "/logs/access.log",
    error_log = "/logs/error.log",
    chroot = "./",
    pid_file = "/run/mongrel2-wsgi.pid",
    default_host = HOST,
    port = 6767
    )
    
handler_wsgi = Handler(send_spec = 'tcp://127.0.0.1:9997',
    send_ident = '0f8813e5-9299-4daa-b03f-8e22b6fb34c3',
    recv_spec = 'tcp://127.0.0.1:9996', recv_ident = '')

# the r'' string syntax means to not interpret any \ chars, for regexes
wsgitest = Host(name = HOST, routes = {
    r'/': handler_wsgi,
    })

main.hosts = [wsgitest]

settings = {"zeromq.threads": 4}

commit([main], settings=settings)
