# -*- coding: utf-8 -*-
"""
Created on Wed Aug 26 09:09:07 2020

@author: 535792
"""

import os
import zipfile
import shutil
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import pandas as pd
from scipy.ndimage.filters import uniform_filter


def _copyfiles_date(root,savepf,dates,workcells,mx1,mx2,needrawdata,combinecsv):
    for date in dates:
        for mx in workcells:
            fps = os.path.join(root,date,mx)
            zip = fps + '.zip'
            if zipfile.is_zipfile(zip):
                with zipfile.ZipFile(zip, 'r') as zipObject:
                    listOfFileNames = zipObject.namelist()
                    for names in listOfFileNames:
                        if '/bandvga/' in names:
                            if needrawdata:
                                zipObject.extract(names,savepf)
                            else:
                                if names.endswith('.csv'):
                                    zipObject.extract(names, savepf)
            else: 
                if os.path.isdir(fps):
                    _copyfiles_recent(fps, savepf, mx, needrawdata)
                else:
                    if mx.lower() == 'mx286': pf = mx2
                    if mx.lower() == 'mx284': pf = mx1
                    _copyfiles_recent(pf, savepf, mx, needrawdata)

    if combinecsv:
        for dirname, dirnames, filenames in os.walk(savepf):
            for file in filenames:
                if file == 'bandvga.csv':
                    pack = dirname.split(os.path.sep)[-2][4:]
                    tester = dirname.split(os.path.sep)[-3][1:3]
                    mdw = dirname.split(os.path.sep)[-3][7:]
                    mx = dirname.split(os.path.sep)[-4]
                    data = pd.read_csv(os.path.join(dirname,file))
                    data['MX'] = mx
                    data['Tester'] = tester 
                    data['MDW'] = mdw
                    data['Pack'] = pack
                    data.to_csv(os.path.join(dirname,'bandvga.csv'),index=False)

        sfp = os.path.join(savepf,'*\*\*\*','bandvga.csv')     
        files = glob.glob(sfp)
        combined_df = pd.concat([pd.read_csv(file) for file in files])
        headers = ['MX', 'Tester', 'MDW', 'Pack', 'trk', 'hd', 'metric', 'val']
        combined_df = combined_df.reindex(columns=headers)
        combined_df = combined_df.rename(columns = {'trk': 'Track', 'hd': 'Head', 
                                                    'metric':'Metric', 'val':'Value'}, inplace = False)
        combined_df.to_csv(os.path.join(savepf,'bandvga_combine.csv'),index=False)


def _copyfiles_recent(fps, savepf, mx, needrawdata):
    for dirname, dirnames, filenames in os.walk(fps):
        for subdirname in dirnames:
            if subdirname == 'bandvga':
                fromDirectory = os.path.join(dirname, subdirname) 
                tester = fromDirectory.split(os.path.sep)[-3]
                pack = fromDirectory.split(os.path.sep)[-2]
                sf = os.path.join(savepf,mx,tester,pack,'bandvga')
                if needrawdata:
                    shutil.copytree(fromDirectory, sf)            
                else:
                    if not os.path.isdir(sf):
                        os.makedirs(sf)
                    shutil.copy(os.path.join(fromDirectory,'bandvga.csv'),sf)
                    
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

def _copyfiles_MSN(MSNp,Packp,root,savepf,mx1,mx2):
    maplist = {'0':'00','1':'01','2':'02','3':'03','4':'04','5':'05','6':'06','7':'07',
               '8':'08','9':'09','A':'10','B':'11','C':'12','D':'13','E':'14',
               'F':'15','G':'16','H':'17','I':'18','J':'19','K':'20','L':'21',
               'M':'22','N':'23','O':'24','P':'25','Q':'26'}
    
    MSNs, Packs, match = _getMSNinfo(MSNp,Packp)

    for MSN in MSNs:
        date = int(MSN[5:8])
        dates = [MSN[4:8],MSN[4]+str("%03d"%(date+1))]
        mx = 'MX' + MSN[12:15]
        hd = int(maplist[MSN[3]])
        hds = [str(hd*2),str(hd*2+1)]
        log = match[MSN]
        pack = 'pack' + log.split('_')[-1]
        tester = 'T' + maplist[MSN[-4]]
        if log[0] == '0':
            mdw = tester + '_mdw' + log.split('_')[0][1:]
        else:
            mdw = tester + '_mdw' + log.split('_')[0]
        for d in dates:
            path = os.path.join(root,d,mx,mdw,pack,'bandvga')
            zip = os.path.join(root,d,mx) + '.zip'
            if zipfile.is_zipfile(zip):
                with zipfile.ZipFile(zip, 'r') as zipObject:
                    listOfFileNames = zipObject.namelist()
                    for names in listOfFileNames:
                        for h in hds:
                            if int(h) < 10:
                                h = '0' + h
                            if 'VGAS_'+ h in names and pack in names:
                                zipObject.extract(names,savepf)
            else:
                if os.path.isdir(path):
                    _copyfile_recent(path,savepf,mx,mdw,pack,hds)
                else:
                    if mx == 'MX286': ad = mx2
                    if mx == 'MX284': ad = mx1 
                    p = os.path.join(ad,mdw,pack,'bandvga')
                    _copyfile_recent(p,savepf,mx,mdw,pack,hds)
                        
def _copyfile_recent(path,savepf,mx,mdw,pack,hds):                        
    for dirname, dirnames, filenames in os.walk(path):
        band = dirname.split(os.path.sep)[-1]
        if '-' in band:
            p = os.path.join(savepf,mx,mdw,pack,'bandvga',band)
            if not os.path.isdir(p):
                os.makedirs(p)
            for file in filenames:
                for h in hds:
                    if int(h) < 10:
                        h = '0' + h
                    if 'VGAS_'+ h in file:
                        shutil.copy(os.path.join(dirname,file),p)

def _movingSigma(processdata,mx,tester,mdw,pack,zone,hd,data,size,threshold,
                 defect_limit1,mean_sigma_limit1,defect_limit2,mean_sigma_limit2):
    winradius = size / 2
    c1 = uniform_filter(data, winradius*2, mode='constant', origin=-winradius)
    c2 = uniform_filter(data*data, winradius*2, mode='constant', origin=-winradius)
    sigma_per_windows = ((c2 - c1*c1 )**.5)[:-winradius * 2 + 1]
    num_defects = len(np.where(np.abs(sigma_per_windows) > threshold)[0])
    mean_sigma = np.mean(sigma_per_windows)
    if num_defects > defect_limit1:
        if mean_sigma > mean_sigma_limit1:
            grading = 0
        else: grading = 1
    elif num_defects > defect_limit2:
        if mean_sigma > mean_sigma_limit2:
            grading = 0       
    else:
        grading = 1
    processdata['Workcell'].append(mx.upper())
    processdata['Tester'].append(tester)
    processdata['MDW'].append(mdw)
    processdata['Pack'].append(pack)
    processdata['Zone'].append(zone)
    processdata['Head'].append(hd)
    processdata['Defects'].append(num_defects)
    processdata['Mean_Sigma'].append("%.2f" % mean_sigma) 
    processdata['Grading'].append(grading)
    return processdata,num_defects, mean_sigma, sigma_per_windows, grading 

def _plotbandvga(path,processdata,data,size,threshold,defect_limit1,mean_sigma_limit1,
                 defect_limit2,mean_sigma_limit2,hd,tester,pack,band,savepf,mdw,mx):
    _,outliers, mean_sigma, filtered, garding = _movingSigma(processdata,mx,tester,mdw,pack,band,hd,data,size,threshold,
                                                             defect_limit1,mean_sigma_limit1,defect_limit2,mean_sigma_limit2)
    fig = plt.figure()
    plt.suptitle('Hd%02d Window-Sigmas vs. Raw VGAS\nMX%s Tester%s Pack%s Band = %s\nOutliers=%d, MeanSigma=%.2f' % \
                 (int(hd), mx, tester, pack, band, outliers, mean_sigma))

    plt.subplot(211)
    plt.ylabel('VGAS Counts') 
    plt.xlabel('VGAS Sample')
    meanv = data.mean()
    plt.ylim([meanv - 50, meanv + 50])
    plt.plot(data)
    plt.subplot(212)
    plt.ylim([0, threshold+15])
    plt.ylabel('Sigma')
    plt.xlabel('Window #')
    plt.hlines(y=threshold, xmin=0, xmax=len(filtered), color='r', linestyles='dashed')
    plt.plot(filtered)
    packn = mdw + '_' + pack
    plotname = packn + '_VGAS_H' + str(hd)
    p = os.path.join(savepf,'bandvga',mx,band)
    if not os.path.isdir(p):
        os.makedirs(p)
    fig.savefig(os.path.join(p,plotname))
    plt.close()

def _getdatainfo(path,size,threshold,defect_limit1,mean_sigma_limit1,defect_limit2,mean_sigma_limit2,output_csv):
    processdata = {}
    headers = ['Workcell', 'Tester', 'MDW', 'Pack', 'Zone', 'Head', 'Defects', 'Mean_Sigma', 'Grading']
    for header in headers:
        processdata[header] = []   
    for dirname, dirnames, filenames in os.walk(savepf):
        for dirn in dirnames:
            if '-' in dirn:
                zone = dirn.split('-')[0] 
                pack = dirname.split(os.path.sep)[-2][4:]
                tester = dirname.split(os.path.sep)[-3][1:3]
                mdw = dirname.split(os.path.sep)[-3][7:]
                mx = dirname.split(os.path.sep)[-4]                
                files = os.listdir(os.path.join(dirname,dirn))
                for fil in files:
                    if '_BandVGA.txt' in fil:
                        hd = int(fil.split('_')[1])
                        data = []
                        with open(os.path.join(dirname,dirn,fil), 'r') as f:
                            for line in f.readlines(): data.append(float(line)) 
                        data = np.array(data)
                        if plot_graph:
                            _plotbandvga(path,processdata,data,win_size,threshold,defect_limit1,mean_sigma_limit1,
                                         defect_limit2,mean_sigma_limit2,hd,tester,pack,zone,savepf,mdw,mx)                                                             
                        _movingSigma(processdata,mx,tester,mdw,pack,zone,hd,data,
                                     size,threshold,defect_limit1,mean_sigma_limit1,defect_limit2,mean_sigma_limit2)
    df = pd.DataFrame(processdata)
    df = df.reindex(columns=headers)
    df.to_csv(os.path.join(savepf,'BandVGA_Processed.csv'),index=False)      

if __name__ == '__main__':

    ################################### USER CONFIG ################################################
    # Note: this script current only supports loading data from one file per run. If there is
    # interest, I can update the script to enable "batch processing" functionality.
    
    # save data address
    savepf = r'C:\data\AGC\trigger'
    # plot&process data location
    savepfl = r'C:\data\AGC\trigger' 
    # server address
    root = r'\\10.11.103.121\mdwb\PRISMTest'
    mx1 = r'\\10.34.35.140\c\data\process\ER72M_5547'
    mx2 = r'\\10.34.35.142\c\data\process\ER72M_5547'
    
    # download files by date:
    dates = ['L114','L115','L116','L117','L118','L119','L120','L121','L122','L123'] 
    workcells = ['MX284']
    # only need csv
    needrawdata = 1
    # combine all bandvga.csv (output bandvga_combine.csv)
    combinecsv = 0
    #_copyfiles_date(root,savepf,dates,workcells,mx1,mx2,needrawdata,combinecsv)
    
    # download by MSN&pack;
    MSNp = r'C:\data\AGC\trigger\MSN.txt'
    Packp = r'C:\data\AGC\trigger\Pack.txt'
    _copyfiles_MSN(MSNp,Packp,root,savepf,mx1,mx2)
        
    # customize bandvga settings
    win_size  = 1500
    threshold = 9.0
    mean_sigma_limit1 = 7.9
    defect_limit1 = 940
    mean_sigma_limit2 = 6.2
    defect_limit2 = 1900
    
    # if need to plot graphs
    plot_graph = 1 
    # if need to output processed data
    output_csv = 1  
    _getdatainfo(savepfl,win_size,threshold,defect_limit1,mean_sigma_limit1,defect_limit2,mean_sigma_limit2,output_csv)
    
    
    ################################################################################################


                                   
            