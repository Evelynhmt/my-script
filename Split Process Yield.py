# -*- coding: utf-8 -*-
"""
Created on Wed Aug 25 11:15:19 2021

@author: 535792
"""

import pandas as pd
import os
import glob
from collections import Counter
from datetime import date, datetime, timedelta


def getinfo(rdata,data,i,t):
     d1 = datetime.strptime(data.iloc[i]['MDW_DATE_TM'], '%m/%d/%Y %H:%M:%S')
     rdata['Date'].append(d1)
     rdata['TA num'].append(data.iloc[i]['TA_NUM'])
     rdata['Workcell'].append(data.iloc[i]['MDW_WORK_CELL'])
     rdata['Tester'].append(t)
     rdata['Pass'].append(data.iloc[i]['MDW_PASS'])
     rdata['HDW Caddy'].append(data.iloc[i]['SRC_CID'])
     rdata['Slot'].append(data.iloc[i]['SRC_LOC'])
     return rdata
    
    
def formthereport(savepf,savep,passbin):
    sfp = os.path.join(savep,'_LotHistorydetails*.csv')
    files = glob.glob(sfp)
    file = max(files, key=os.path.getctime)
    data = pd.read_csv(os.path.join(savep,file)) 
    binlist = pd.read_csv(os.path.join(savep,'SPlit Process Bin List.csv'))
    headers = ['Date','TA num','Workcell','Tester','HDW Caddy','Slot','Bin','Pass','Type']
    rdata = {}
    for header in headers:
        rdata[header] = []
    i = 0
    for t in data['MDW_TESTER']:
        if t.lower() != 'a' and t.lower() != 'b':
            mdw_bin = data.iloc[i]['MDW_BIN']
            if mdw_bin[:4] == 'C000':
                rdata['Bin'].append(mdw_bin)
                rdata['Type'].append('C')
                getinfo(rdata,data,i,t)
            elif mdw_bin[0] == 'C':
                rdata['Bin'].append(mdw_bin[:4])
                rdata['Type'].append('C')
                getinfo(rdata,data,i,t)
            elif mdw_bin[0] == 'S':
                try: 
                   if int(mdw_bin[-3:]) == 0:
                       rdata['Bin'].append(mdw_bin[:4])
                       rdata['Type'].append('S')
                       getinfo(rdata,data,i,t)
                except:
                    if passbin in mdw_bin:
                        rdata['Bin'].append(mdw_bin[:5])
                        rdata['Type'].append('S')
                        getinfo(rdata,data,i,t)
                    elif mdw_bin[-3] == 'A' or mdw_bin[-3] == 'B' or mdw_bin[-3] == 'C':
                        rdata['Bin'].append(mdw_bin[:4])
                        rdata['Type'].append('S')
                        getinfo(rdata,data,i,t)
            elif mdw_bin.lower() == 'da03888':
                rdata['Bin'].append(mdw_bin)
                rdata['Type'].append('S')
                getinfo(rdata,data,i,t)                
        i = i + 1
        
    df = pd.DataFrame(rdata)
  
    j = 0
    for bin in df['Bin']:
        k = 0
        for bin2 in binlist['Bin']:
            if bin.lower() == bin2.lower():
                df.ix[j,'Description'] = binlist.iloc[k]['Desc']
                break
            k = k + 1
        if k == len(binlist):
            df.ix[j,'Description'] = bin
        j = j +1
    df = df.reindex(columns=(headers + ['Description']))
    df.to_csv(os.path.join(savepf,'RawYielddata.csv'),index=False)
    
    cfirst,cfinal,sfirst,sfinal = reorg_data(df,headers)
    writer1 = pd.ExcelWriter(os.path.join(savepf,'Yield_by_MX.xlsx'), engine='xlsxwriter')
    writer2 = pd.ExcelWriter(os.path.join(savepf,'Yield_by_TA.xlsx'), engine='xlsxwriter')
    writer1, writer2 = calculateyield('MDWC first Pass',cfirst,writer1,writer2)
    writer1, writer2 = calculateyield('MDSW first Pass',sfirst,writer1,writer2)
    writer1, writer2 = calculateyield('MDWC final Pass',cfinal,writer1,writer2)
    writer1, writer2 = calculateyield('MDSW final Pass',sfinal,writer1,writer2)
    writer1.save()
    writer2.save()
    
        
def reorg_data(df,headers):
    sfirst = pd.DataFrame(columns=headers + ['Description'])
    sf = pd.DataFrame(columns=headers + ['Description'])
    sfinal = pd.DataFrame(columns=headers + ['Description'])
    cfirst = pd.DataFrame(columns=headers + ['Description'])
    cf = pd.DataFrame(columns=headers + ['Description'])
    cfinal = pd.DataFrame(columns=headers + ['Description'])
    l = 0
    for type in df['Type']:
        if type == 'S':
            if df.iloc[l]['Pass'] == 1 or df.iloc[l]['Pass'] == 2:
                sfirst = sfirst.append(df.loc[l], ignore_index=True)
            sf = sf.append(df.loc[l], ignore_index=True)
        else:
            if df.iloc[l]['Pass'] == 1:
                cfirst = cfirst.append(df.loc[l], ignore_index=True)
            cf = cf.append(df.loc[l], ignore_index=True)
        l = l + 1
    cf = cf.sort_values(by=['Workcell','TA num','HDW Caddy','Slot','Date'])
    sf = sf.sort_values(by=['Workcell','TA num','HDW Caddy','Slot','Date']) 
    cfinal = finaldata(cfinal,cf)
    sfinal = finaldata(sfinal,sf)
    return cfirst,cfinal,sfirst,sfinal    
    

def finaldata(fdf,rdf):    
    m = 0
    for slot in rdf['Slot']:
        if m == len(rdf['Slot'])-1:
            fdf.loc[m] = rdf.iloc[m]
        elif slot != rdf.iloc[m+1]['Slot']:
            fdf.loc[m] = rdf.iloc[m]
        elif rdf.iloc[m]['HDW Caddy'] != rdf.iloc[m+1]['HDW Caddy']:
            fdf.loc[m] = rdf.iloc[m]
        m = m + 1
    return fdf


def calculateyield(name,data0,writer1,writer2):
    data0 = data0.drop(['HDW Caddy','Slot','Date','Pass','Type','Bin'], axis=1)
    s1 = pd.pivot_table(data0, index=['Description'],columns=['Workcell','Tester'], aggfunc='count').fillna(int(0))
    s2 = pd.pivot_table(data0, index=['Description'],columns=['TA num','Workcell'], aggfunc='count').fillna(int(0))
    s1 = removebin(s1)
    s2 = removebin(s2)
    TA = []
    mx = []
    n = 0
    for co in s2.columns:
        TA.append(co[0])
        n = n + 1
    for item in Counter(TA).items():
        ta = item[0]
        no = item[1]
        if no > 1:
            s2[(ta,'Total')] =  s2.loc[:,pd.IndexSlice[ta,:]].values.sum(axis=1)
    s2 = s2.reindex(s2.columns.sort_values(ascending=[True, True]), axis=1)
    total = s2.values.sum(axis=0)
    s2.loc[:,:] = s2.loc[:,:].div(s2.values.sum(axis=0), axis=1)
    s2.replace(0, '', inplace=True)
    s2.loc['Grant Total',:] = total

    m = 0
    for co1 in s1.columns:
        mx.append(co1[0])
        m = m + 1
    for item1 in Counter(mx).items():
        mx = item1[0]
        s1[(mx,'Total')] =  s1.loc[:,pd.IndexSlice[mx,:]].values.sum(axis=1)
    s1 = s1.reindex(s1.columns.sort_values(ascending=[True, True]), axis=1)
    total1 = s1.values.sum(axis=0)
    s1.loc[:,:] = s1.loc[:,:].div(s1.values.sum(axis=0), axis=1)
    s1.replace(0, '', inplace=True)
    s1.loc['Grant Total',:] = total1
    s1.to_excel(writer1,sheet_name= name)
    s2.to_excel(writer2,sheet_name= name)
    return writer1, writer2


def removebin(ndf):
    ndf.columns = ndf.columns.droplevel()
    try:
        ndf = ndf.drop('Detcr Noise grade B_MDSW')
    except:
        pass
    try:
        ndf = ndf.drop('Align')
    except:
        pass
    try:
        ndf = ndf.drop('Geo')
    except:
        pass
    return ndf
  

if __name__ == '__main__':

    ################################### USER CONFIG ################################################
  
    # save processed data address
    savepf = r'C:\00\SplitYield\Daily Yield'
    # raw data location
    savep = r'C:\00\SplitYield'
    passbin = 'S34'

    formthereport(savepf,savep,passbin)


    
