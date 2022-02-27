from pyobigram.utils import sizeof_fmt,get_file_size,createID
from pyobigram.client import ObigramClient,Downloader,inlineQueryResultArticle
from MoodleClient import MoodleClient

import config
import zipfile
import os
import infos
import xdlink
import mediafire
from megacli.mega import Mega
import megacli.megafolder as megaf
import megacli.mega
import datetime
import time
import youtube
import NexCloudClient

def downloadFile(downloader,filename,currentBits,totalBits,speed,args,stop=False):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,tid=thread.id)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def uploadFile(filename,currentBits,totalBits,speed,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        downloadingInfo = infos.createUploading(filename,totalBits,currentBits,speed,originalfile)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def processUploadFiles(filename,filesize,files,update,bot,message,thread=None):
    try:
        bot.editMessageText(message,'🤜Preparando Para Subir☁...')
        evidence = None
        fileid = None
        cloudtype = config.getUser(update.message.sender.username)['cloudtype']
        if cloudtype == 'moodle':
            client = MoodleClient(config.getUser(update.message.sender.username)['moodle_user'],config.getUser(update.message.sender.username)['moodle_password'],config.getUser(update.message.sender.username)['moodle_host'],config.getUser(update.message.sender.username)['moodle_repo_id'])
            loged = client.login()
            itererr = 0
            if loged:
                evidences = client.getEvidences()
                evidname = str(filename).split('.')[0]
                for evid in evidences:
                    if evid['name'] == evidname:
                        evidence = evid
                        break
                if evidence is None:
                    evidence = client.createEvidence(evidname)
                originalfile = ''
                if len(files)>1:
                    originalfile = filename
                for f in files:
                    f_size = get_file_size(f)
                    resp = None
                    iter = 0
                    while resp is None:
                          fileid,resp = client.upload_file(f,evidence,fileid,progressfunc=uploadFile,args=(bot,message,originalfile,thread))
                          iter += 1
                          if iter>=10:
                              break
                    os.unlink(f)
                try:
                    client.saveEvidence(evidence)
                except:pass
                return client
            else:
                bot.editMessageText(message,'❌Error En La Pagina❌')
        elif cloudtype == 'cloud':
            bot.editMessageText(message,'🤜Subiendo ☁ Espere Mientras... 😄')
            host = config.getUser(update.message.sender.username)['moodle_host']
            user = config.getUser(update.message.sender.username)['moodle_user']
            passw = config.getUser(update.message.sender.username)['moodle_password']
            remotepath = config.getUser(update.message.sender.username)['dir']
            client = NexCloudClient.NexCloudClient(user,passw,host)
            loged = client.login()
            if loged:
               originalfile = ''
               if len(files)>1:
                    originalfile = filename
               for f in files:
                   client.upload_file(f,path=remotepath,progressfunc=uploadFile,args=(bot,message,originalfile,thread))
                   os.unlink(f)
               return client
        return None
    except Exception as ex:
        bot.editMessageText(message,'❌Error En La Pagina❌')


def processFile(update,bot,message,file,thread=None):
    file_size = get_file_size(file)
    getUser = config.getUser(update.message.sender.username)
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    client = None
    findex = 0
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(file,file_size,max_file_size)
        bot.editMessageText(message,compresingInfo)
        zipname = str(file).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname,max_file_size)
        zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file)
        zip.close()
        mult_file.close()
        client = processUploadFiles(file,file_size,mult_file.files,update,bot,message)
        try:
            os.unlink(file)
        except:pass
        file_upload_count = len(zipfile.files)
    else:
        client = processUploadFiles(file,file_size,[file],update,bot,message)
        file_upload_count = 1
    bot.editMessageText(message,'🤜Preparando Archivo📄...')
    evidname = ''
    files = []
    if client:
        try:
            evidname = str(file).split('.')[0]
            txtname = evidname + '.txt'
            evidences = client.getEvidences()
            for ev in evidences:
                if ev['name'] == evidname:
                   files = ev['files']
                   break
                if len(ev['files'])>0:
                   findex+=1
            client.logout()
        except:pass
        bot.deleteMessage(message.chat.id,message.message_id)
        finishInfo = infos.createFinishUploading(file,file_size,max_file_size,file_upload_count,file_upload_count,findex)
        filesInfo = infos.createFileMsg(file,files)
        bot.sendMessage(message.chat.id,finishInfo+'\n'+filesInfo,parse_mode='html')
        if len(files)>0:
            sendTxt(txtname,files,update,bot)
    else:
        bot.editMessageText(message,'❌Error En La Pagina❌')

def ddl(update,bot,message,url,file_name='',thread=None):
    downloader = Downloader(filename=file_name)
    file = downloader.downloadFile(url,progressfunc=downloadFile,args=(bot,message,thread))
    if not downloader.stoping:
        processFile(update,bot,message,file)

def megadl(update,bot,message,megaurl,thread=None):
    megadl = megacli.mega.Mega({'verbose': True})
    megadl.login()
    try:
        info = megadl.get_public_url_info(megaurl)
        file_name = info['name']
        megadl.download_url(megaurl,dest_path=None,dest_filename=file_name,progressfunc=downloadFile,args=(bot,message,thread))
        if not megadl.stoping:
            processFile(update,bot,message,file_name,thread=thread)
    except:
        files = megaf.get_files_from_folder(megaurl)
        for f in files:
            file_name = f['name']
            megadl._download_file(f['handle'],f['key'],dest_path=None,dest_filename=file_name,is_public=False,progressfunc=downloadFile,args=(bot,message,thread),f_data=f['data'])
            if not megadl.stoping:
                processFile(update,bot,message,file_name,thread=thread)
        pass
    pass

def sendTxt(name,files,update,bot):
                txt = open(name,'w')
                fi = 0
                for f in files:
                    separator = ''
                    if fi < len(files)-1:
                        separator += '\n'
                    txt.write(f['directurl']+separator)
                    fi += 1
                txt.close()
                bot.sendFile(update.message.chat.id,name)
                os.unlink(name)

def onmessage(update,bot:ObigramClient):
    try:
        thread = bot.this_thread
        username = update.message.sender.username

        msgText = ''
        try: msgText = update.message.text
        except:pass

        if username not in config.PV_USERS:
            bot.sendMessage(update.message.chat.id,'❌No Tienes Acceso Al Bot❌')
            return

        if config.getUser(username) is None:
            config.createUser(username)
            config.saveDB()
            reply_msg = '😃Bienvenido ' + username + ' 😃\n'
            reply_msg+= 'Nesesita configurar su cuenta de moodle\n'
            reply_msg+= 'Ejemplo : /account user,password\n'
            reply_msg+= 'Puede enviar /myuser para revisar su usuario'
            bot.sendMessage(update.message.chat.id,reply_msg)
        else:
            if '/myuser' != msgText and '/tutorial' not in msgText and '/cancel' not in msgText and '/account' not in msgText and '/host' not in msgText and '/repo' not in msgText and '/cloud' not in msgText and '/dir' not in msgText:
                configmsg = '😣Primero Configure Su Cuenta De Moodle😣\n⚙️/myuser Para Configurar⚙️'
                if config.getUser(username)['moodle_user'] == '':
                    bot.sendMessage(update.message.chat.id,configmsg)
                    return
                if config.getUser(username)['moodle_password'] == '':
                    bot.sendMessage(update.message.chat.id,configmsg)
                    return


        # comandos de admin
        if '/adduser' in msgText:
            isadmin = config.isAdmin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    config.PV_USERS.append(user)
                    msg = '😃Genial @'+user+' ahora tiene acceso al bot👍'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'❌Error en el comando /adduser username❌')
            else:
                bot.sendMessage(update.message.chat.id,'❌No Tiene Permiso❌')
            return
        if '/banuser' in msgText:
            isadmin = config.isAdmin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    if user == username:
                        bot.sendMessage(update.message.chat.id,'❌No Se Puede Banear Usted❌')
                        return
                    config.PV_USERS.remove(user)
                    msg = '🦶Fuera @'+user+' Baneado❌'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'❌Error en el comando /banuser username❌')
            else:
                bot.sendMessage(update.message.chat.id,'❌No Tiene Permiso❌')
            return
        if '/getdb' in msgText:
            isadmin = config.isAdmin(username)
            if isadmin:
                bot.sendMessage(update.message.chat.id,'Base De Datos👇')
                bot.sendFile(update.message.chat.id,'database.udb')
            else:
                bot.sendMessage(update.message.chat.id,'❌No Tiene Permiso❌')
            return
        # end

        # comandos de usuario
        if '/tutorial' in msgText:
            tuto = open('tuto.txt','r')
            bot.sendMessage(update.message.chat.id,tuto.read())
            tuto.close()
            return
        if '/myuser' in msgText:
            getUser = config.getUser(username)
            if getUser:
                statInfo = infos.createStat(username,getUser,config.isAdmin(username))
                bot.sendMessage(update.message.chat.id,statInfo)
                return
        if '/zips' in msgText:
            getUser = config.getUser(username)
            if getUser:
                try:
                   size = int(str(msgText).split(' ')[1])
                   getUser['zips'] = size
                   config.saveDataUser(username,getUser)
                   config.saveDB()
                   msg = '😃Genial los zips seran de '+ sizeof_fmt(size*1024*1024)+' las partes👍'
                   bot.sendMessage(update.message.chat.id,msg)
                except:
                   bot.sendMessage(update.message.chat.id,'❌Error en el comando /zips size❌')
                return
        if '/account' in msgText:
            try:
                account = str(msgText).split(' ',2)[1].split(',')
                user = account[0]
                passw = account[1]
                getUser = config.getUser(username)
                if getUser:
                    getUser['moodle_user'] = user
                    getUser['moodle_password'] = passw
                    config.saveDataUser(username,getUser)
                    config.saveDB()
                    statInfo = infos.createStat(username,getUser,config.isAdmin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌Error en el comando /account user,password❌')
            return
        if '/host' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                host = cmd[1]
                getUser = config.getUser(username)
                if getUser:
                    getUser['moodle_host'] = host
                    config.saveDataUser(username,getUser)
                    config.saveDB()
                    statInfo = infos.createStat(username,getUser,config.isAdmin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌Error en el comando /host moodlehost❌')
            return
        if '/repo' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = int(cmd[1])
                getUser = config.getUser(username)
                if getUser:
                    getUser['moodle_repo_id'] = repoid
                    config.saveDataUser(username,getUser)
                    config.saveDB()
                    statInfo = infos.createStat(username,getUser,config.isAdmin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌Error en el comando /repo id❌')
            return
        if '/cloud' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = cmd[1]
                getUser = config.getUser(username)
                if getUser:
                    getUser['cloudtype'] = repoid
                    config.saveDataUser(username,getUser)
                    config.saveDB()
                    statInfo = infos.createStat(username,getUser,config.isAdmin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌Error en el comando /cloud (moodle or cloud)❌')
            return
        if '/dir' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = cmd[1]
                getUser = config.getUser(username)
                if getUser:
                    getUser['dir'] = repoid + '/'
                    config.saveDataUser(username,getUser)
                    config.saveDB()
                    statInfo = infos.createStat(username,getUser,config.isAdmin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌Error en el comando /dir folder❌')
            return
        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_',2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop',True)
                time.sleep(3)
                bot.editMessageText(msg,'❌Tarea Cancelada❌')
            except Exception as ex:
                print(str(ex))
            return
        #end

        message = bot.sendMessage(update.message.chat.id,'🕰Procesando🕰...')

        thread.store('msg',message)

        if '/start' in msgText:
            start_msg = 'Bot          : TGMoodleFree v0.4\n'
            start_msg+= 'Desarrollador: @sinarrobamamawebo\n'
            start_msg+= 'Uso          :Envia Enlaces De Descarga Para Procesar\n'
            bot.editMessageText(message,start_msg)
        elif '/files' == msgText and config.getUser(update.message.sender.username)['cloudtype']=='moodle':
             client = MoodleClient(config.getUser(update.message.sender.username)['moodle_user'],config.getUser(update.message.sender.username)['moodle_password'],config.getUser(update.message.sender.username)['moodle_host'],config.getUser(update.message.sender.username)['moodle_repo_id'])
             loged = client.login()
             if loged:
                 files = client.getEvidences()
                 filesInfo = infos.createFilesMsg(files)
                 bot.editMessageText(message,filesInfo)
                 client.logout()
             else:
                bot.editMessageText(message,'❌Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
        elif '/txt_' in msgText and config.getUser(update.message.sender.username)['cloudtype']=='moodle':
             findex = str(msgText).split('_')[1]
             findex = int(findex)
             client = MoodleClient(config.getUser(update.message.sender.username)['moodle_user'],config.getUser(update.message.sender.username)['moodle_password'],config.getUser(update.message.sender.username)['moodle_host'],config.getUser(update.message.sender.username)['moodle_repo_id'])
             loged = client.login()
             if loged:
                 evidences = client.getEvidences()
                 evindex = evidences[findex]
                 txtname = evindex['name']+'.txt'
                 sendTxt(txtname,evindex['files'],update,bot)
                 client.logout()
                 bot.editMessageText(message,'TxT Aqui👇')
             else:
                bot.editMessageText(message,'❌Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
             pass
        elif '/del_' in msgText and config.getUser(update.message.sender.username)['cloudtype']=='moodle':
            findex = int(str(msgText).split('_')[1])
            client = MoodleClient(config.getUser(update.message.sender.username)['moodle_user'],config.getUser(update.message.sender.username)['moodle_password'],config.getUser(update.message.sender.username)['moodle_host'],config.getUser(update.message.sender.username)['moodle_repo_id'])
            loged = client.login()
            if loged:
                evfile = client.getEvidences()[findex]
                client.deleteEvidence(evfile)
                client.logout()
                bot.editMessageText(message,'Archivo Borrado 🦶')
            else:
                bot.editMessageText(message,'❌Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
        elif 'http' in msgText:
            url = msgText
            filename = ''
            if 'youtube' in url or 'youtu.be' in url:
                try:
                    data = youtube.getVideoData(url)
                    if data:
                        url = data['url']
                        filename = data['name']
                    else:
                        bot.editMessageText(message,'❌Error Link No Me Sirve❌')
                        return
                except:
                    bot.editMessageText(message,'❌No Soporto Carpetas De Mediafire❌')
                    return
            if 'mediafire' in url:
                try:
                    url = mediafire.get(url)
                except:
                    bot.editMessageText(message,'❌No Soporto Carpetas De Mediafire❌')
                    return
            elif 'mega.nz' in msgText:
                try:
                    megadl(update,bot,message,url,thread=thread)
                except Exception as ex:
                    print(str(ex))
                return
            ddl(update,bot,message,url,file_name=filename,thread=thread)
        else:
            bot.editMessageText(message,'😵No se pudo procesar😵')
    except Exception as ex:
           bot.sendMessage(update.message.chat.id,'❌'+str(ex)+'❌')
           print(str(ex))


def main():
    bot = ObigramClient(config.BOT_TOKEN)
    bot.onMessage(onmessage)
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except:
        config.loadDB()
        main()
