BOT_TOKEN = '5208012497:AAFJOOgQshcqPaMJWoLBcOA59h8HX5PKC0Q'
PV_USERS = ['Zer09810']

USERS = {Zer09810}
def saveDB():
    import os
    name = 'database.udb'
    dbfile = open(name,'w')
    i = 0
    for user in USERS:
        separator = ''
        if i < len(USERS)-1:
            separator = '\n'
        dbfile.write(user+'='+str(USERS[user]) + separator)
        i+=1
    dbfile.close()

def createUser(name):
    import time
    USERS[name] = {'dir':'','cloudtype':'moodle','moodle_host':'https://moodle.uclv.edu.cu/','moodle_repo_id':4,'moodle_user':'','moodle_password':'','isadmin':0,'zips':100}

def getUser(name):
    try:
        return USERS[name]
    except:
        return None

def saveDataUser(user,data):
    USERS[user] = data

def isAdmin(user):
    User = getUser(user)
    if User:
        return User['isadmin']==1
    return False

def loadDB():
    import os
    import json
    name = 'database.udb'
    dbfile = open(name,'r')
    lines = dbfile.read().split('\n')
    dbfile.close()
    for lin in lines:
        if lin == '':continue
        tokens = lin.split('=')
        user = tokens[0]
        PV_USERS.append(user)
        data = json.loads(str(tokens[1]).replace("'",'"'))
        USERS[user] = data

#load db to init
loadDB()
