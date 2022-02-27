import requests
import os
import requests_toolbelt as rt
from requests_toolbelt import MultipartEncoderMonitor
from requests_toolbelt import MultipartEncoder
from functools import partial
import time
from bs4 import BeautifulSoup


class NexCloudClient(object):
    def __init__(self, user,password,path='https://nube.uclv.cu/'):
        self.user = user
        self.password = password
        self.session = requests.Session()
        self.path = path

    def login(self):
        loginurl = self.path + 'index.php/login'
        resp = self.session.get(loginurl)
        soup = BeautifulSoup(resp.text,'html.parser')
        requesttoken = soup.find('head')['data-requesttoken']
        timezone = 'America/Mexico_City'
        timezone_offset = '-5'
        payload = {'user':self.user,'password':self.password,'timezone':timezone,'timezone_offset':timezone_offset,'requesttoken':requesttoken};
        resp = self.session.post(loginurl, data=payload)
        print(resp.text)
        soup = BeautifulSoup(resp.text,'html.parser')
        title = soup.find('div',attrs={'id':'settings'})
        if title:
            return True
        return False

    def upload_file(self,file,path='',progressfunc=None,args=()):
        files = self.path + 'index.php/apps/files/'
        uploadUrl = self.path + 'remote.php/webdav/'+ path + file
        resp = self.session.get(files)
        soup = BeautifulSoup(resp.text,'html.parser')
        requesttoken = soup.find('head')['data-requesttoken']
        f  = open(file,'rb')
        upload_file = {'file':(file,f,'application/octet-stream')}
        class CloudUpload:
                def __init__(self, func,filename,args):
                    self.func = func
                    self.args = args
                    self.filename = filename
                    self.time_start = time.time()
                    self.time_total = 0
                    self.speed = 0
                    self.last_read_byte = 0
                def __call__(self,monitor):
                    self.speed += monitor.bytes_read - self.last_read_byte
                    self.last_read_byte = monitor.bytes_read
                    tcurrent = time.time() - self.time_start
                    self.time_total += tcurrent
                    self.time_start = time.time()
                    if self.time_total>=1:
                            if self.func:
                                 self.func(self.filename,monitor.bytes_read,monitor.len,self.speed,self.args)
                            self.time_total = 0
                            self.speed = 0
        #encoder = rt.MultipartEncoder(upload_file)
        #progrescall = CloudUpload(progressfunc,file,args)
        #callback = partial(progrescall)
        #monitor = MultipartEncoderMonitor(encoder,callback=callback)
        #resp = self.session.put(uploadUrl,data=monitor,headers={'requesttoken':requesttoken})
        resp = self.session.put(uploadUrl,data=f,headers={'requesttoken':requesttoken})
        f.close()
        retData = {'upload':False}
        if resp.status_code == 201:
            retData = {'upload':True,'msg':file + ' Upload Complete!','url':str(resp.url).replace('//','/')}
        if resp.status_code == 204:
            retData = {'upload':False,'msg':file + ' Exist!','url':str(resp.url).replace('//','/')}
        if resp.status_code == 409:
            retData = {'upload':False,'msg':'Not ' + user + ' Folder Existent!'}
        return retData


#client = NexCloudClient('cvgonzalez','pusipo-759')
#loged = client.login()
#if loged:
#    client.uploadfile('requirements.txt')
#    print('loged')
#    pass