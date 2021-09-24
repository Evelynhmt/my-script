# -*- coding: utf-8 -*-
"""
Created on Tue Aug 25 15:28:22 2020

@author: 535792
"""
import os
import zipfile 
import shutil
import matplotlib.pyplot as plt
import numpy as np
import os

def _getMSNinfo(MSNp,Packp):  
    MSNs = []
    Packs = []
    with open(MSNp, 'r') as f:
        for line in f.read().splitlines(): MSNs.append(line)
    with open(Packp, 'r') as f:
        for line in f.read().splitlines(): Packs.append(line)
    match = {}
    i = 0
    for MSN in MSNs:
        match[MSN] = Packs[i]
        i+=1
    return MSNs, Packs, match
 
def _copyfiles_MSN(MSNp,Packp,root,savef,maplist):
    MSNs, Packs, match = _getMSNinfo(MSNp,Packp)
    for MSN in MSNs:
        date = int(MSN[5:8])
        dates = [MSN[4:8],MSN[4]+str("%03d"%(date+1))]
        mx = 'MX' + MSN[12:15]
        log = match[MSN]
        pack = 'pack' + log.split('_')[-1]
        tester = 'T' + maplist[MSN[-4]]               
        if log[0] == '0':
            mdw = tester + '_mdw' + log.split('_')[0][1:]
        else:
            mdw = tester + '_mdw' + log.split('_')[0]
        for d in dates:
            path = os.path.join(root,d,mx,mdw,pack,'sqz')
            zip = os.path.join(root,d,mx) + '.zip'
            if zipfile.is_zipfile(zip):
                with zipfile.ZipFile(zip, 'r') as zipObject:
                    listOfFileNames = zipObject.namelist()
                    for names in listOfFileNames:
                        for z in zone:
                            if 'sqz__' in names and z in names and pack in names:
                                zipObject.extract(names,savepf)  
            else:
                _unziprecent(path,savef,mx,mdw,pack)
                if MSN[12:15] == '286':
                    lpath = os.path.join(pcf1,mdw,pack,'sqz')
                else:
                    lpath = os.path.join(pcf2,mdw,pack,'sqz')
                _unziprecent(lpath,savef,mx,mdw,pack)
                    
    for dirname, dirnames, filenames in os.walk(savepf):
        for file in filenames:
            if 'sqz' in file and '.zip' in file:
                folder = file[:-4]
                with zipfile.ZipFile(os.path.join(dirname,file), 'r') as zipObject:
                    FileNames = zipObject.namelist()
                    for name in FileNames: 
                        if '_VGA.txt' in name:
                            path = os.path.join(dirname,folder)
                            if not os.path.isdir(path):
                                os.makedirs(path)
                            with zipObject.open(name) as zf, open(os.path.join(
                                    path,os.path.basename(name)), 'w') as f:
                                shutil.copyfileobj(zf, f)                        
                        
def _unziprecent(path,savef,mx,mdw,pack):
    for dirname, dirnames, filenames in os.walk(path):
        for file in filenames:
            for z in zone:
                if z in file:
                    location = os.path.join(savef,mx,mdw,pack,'sqz')
                    if not os.path.isdir(location):
                        os.makedirs(location)
                    shutil.copy(os.path.join(dirname,file),location)

def _plotgraph(track,sector,fp,MSNp,Packp,maplist):
    for dirname, dirnames, filenames in os.walk(fp):
        AGCData = {}
        heads = []
        if 'sqz_' in dirname:
            for file in filenames:
                name = file.split('_')[2]
                zone = dirname.split(os.path.sep)[-1][-3:]
                pack = dirname.split(os.path.sep)[-3][4:]
                tester = dirname.split(os.path.sep)[-4][1:3]
                mdw = dirname.split(os.path.sep)[-4][7:]
                mx = dirname.split(os.path.sep)[-5]
                path = os.path.join(fp,'sqzplot','FullPack',mx)
                if not os.path.isdir(path):
                    os.makedirs(path)
                heads.append(name)
                data = []
                with open(os.path.join(dirname,file), 'r') as f:
                    for line in f.readlines(): data.append(float(line))  
                data = np.array(data)
                if name in AGCData.keys():
                    AGCData[name] = AGCData[name] + data
                else:
                    AGCData[name] = data
            times = {i:heads.count(i) for i in heads}
            for head in AGCData.keys():
                result = np.array(AGCData[head] / times[head])
                result.shape = (track,sector)
                # datap = np.array([result[i:i+n] for i in range(0, len(result), n)])
                dataFFT = np.fft.fft(result, None, axis = 1) 
                harmonicsToRemove=[1,2,3,4,5,6,7,8]
                # Remove requested harmonics (including DC if specified)
                for harmonic in harmonicsToRemove:                                  
                    dataFFT[:,harmonic] = 0                                 
                    if harmonic != 0:  
                        dataFFT[:,result.shape[1]-harmonic] = 0
                # Recreate time-domain filtered data
                data = np.array(np.fft.ifft(dataFFT, None, axis = 1).real)
                data.shape = (track*sector)
                AGCSigma = data.std()
                AGCMean = data.mean()
                data.shape = (track,sector)
                dataf = data.T
                fig = plt.figure()
                plt.suptitle('AGCPlot MX%s Tester%02d Pack%s Zone%s\nHead%s Mean: %03d Sigma: %.3f'% \
                             (mx[2:], int(tester), pack, zone[2:], head[2:], int(AGCMean), AGCSigma))
                plt.subplot(111)
                plt.ylabel('VGAS Counts')
                plt.ylim([AGCMean-40, AGCMean+40]) 
                plt.xlabel('sector')
                plt.grid()
                plt.plot(dataf)
                plotname = mdw + '_' + pack + '_AGC_' + head +'_' + zone
                fig.savefig(os.path.join(path,plotname))
                plt.close()  
                               
    MSNs, Packs, match = _getMSNinfo(MSNp,Packp)
    for MSN in MSNs:
        mx = 'MX' + MSN[12:15]
        p = os.path.join(fp,'sqzplot','SelectHd',mx)
        if not os.path.isdir(p):
            os.makedirs(p)
        path = os.path.join(fp,'sqzplot','FullPack',mx)
        log = match[MSN]
        if log[0] == '0':
            log = log[1:]
        hd = int(maplist[MSN[3]])*2
        if hd < 10:
            hd1 = maplist[str(hd)]
            hd2 = maplist[str(hd + 1)]
        else:
            hd1 = str(hd)
            hd2 = str(hd + 1)
        hds = ['hd'+ hd1,'hd'+ hd2]
        graphs = os.listdir(path)
        for graph in graphs:
            for hd in hds:
                if log in graph and hd in graph:
                    shutil.copy(os.path.join(path,graph),p)
     
                    
if __name__ == '__main__':
    
    ################################### USER CONFIG ################################################
    # Note: this script current only supports loading data from one file per run. If there is
    # interest, I can update the script to enable "batch processing" functionality.
    maplist = {'0':'00','1':'01','2':'02','3':'03','4':'04','5':'05','6':'06','7':'07',
               '8':'08','9':'09','A':'10','B':'11','C':'12','D':'13','E':'14',
               'F':'15','G':'16','H':'17','I':'18','J':'19','K':'20','L':'21',
               'M':'22','N':'23','O':'24','P':'25','Q':'26'}
    
    # save data address
    savepf = r'C:\ER\MX286\M633_5\agcsigma'
    # server address
    root = r'\\10.11.103.121\mdwb\PRISMTest'
    pcf1 = r'\\10.34.35.142\c\data\process\ER72M_5547'
    pcf2 = r'\\10.34.35.140\c\data\process\ER72M_5547'
    MSNp = r'C:\ER\MX286\M633_5\agcsigma\MSNp.txt'
    Packp = r'C:\ER\MX286\M633_5\agcsigma\Packp.txt'
    sector = 416
    track = 32
    zone = ['zn0']
    
    # download by MSN&pack  
    _copyfiles_MSN(MSNp,Packp,root,savepf,maplist)
    
    # plotting AGC graphs with raw data in savepf
    _plotgraph(track,sector,savepf,MSNp,Packp,maplist)
    
    ################################################################################################
