import sys
import os
import glob
import numpy as np
import pandas as pd
import xarray as xr
import argparse
import re
import urllib.request
import f90nml

def check_url(url):
  try:
    urlcode = urllib.request.urlopen(url).getcode()
    result = True
  except:
    result = False
  return result

runs = []
path_datas = []

# Stephan's experiments
path_exps = '/work/mh0287/m211032/Icon/Git_Icon/icon.oes.20200506/experiments/'
path_datas += glob.glob(path_exps+'/*')
path_exps = '/work/mh0287/m211032/Icon/Abl_Git_mh0287/icon.oes.20191023/experiments/'
path_datas += glob.glob(path_exps+'/slo122*')
path_exps = '/work/mh0287/m211032/Icon/Abl_Git_mh0287/icon.oes.20191216/experiments/'
path_datas += glob.glob(path_exps+'/slo*')
# Dian's experiments
path_exps = '/work/mh0033/m300466/icon-ruby/icon-ruby2b/experiments/'
path_datas += glob.glob(path_exps+'/*')

# get run-name and sort out runs which do not start with appropriate shortcut
path_datas_new = []
for nn, path_data in enumerate(path_datas):
  run = path_data.split('/')[-1]
  if run.startswith('slo') or run.startswith('dap'):
    runs.append(run)
    #path_data.append(path_data)
    #path_datas[nn] = path_data+'/'
    path_datas_new.append( path_data+'/' )
path_datas = path_datas_new

df = pd.DataFrame({'run': runs, 'path_data': path_datas})

# --- read namelists (loop over all simulations)
for nn in range(df.shape[0]):
#for nn in range(1):
  # --- ocean namelist
  fpath_nml = df.loc[nn,'path_data']+'NAMELIST_'+df.loc[nn,'run']+'_oce'

  if os.path.exists(fpath_nml):
    pass
  else:
    print(f'::: Warning: {fpath_nml} does not exist!:::')
    continue

  if True:
    # ------ open namelist
    nml = f90nml.read(fpath_nml)
    
    # ------ go through all sections (sub-namelists)
    D = dict()
    for nml_sec in nml.keys():
      if nml_sec=='output_nml':
        continue
      for entr in nml[nml_sec]:
        if entr=='dzlev_m':
          continue
        try:
          D[entr] = {nml[nml_sec][entr]}
        except:
          print(f'xx  {entr}')
          pass
    
    # ------ add namelist values to pandoc data frame
    for key in D.keys():
      try:
        ll = list(D[key])
        if len(ll)==1:
          D[key] = ll[0]
        else:
          D[key] = ll
        if not key in df.columns.tolist():
          df[key] = np.nan
        df.loc[nn,key] = D[key]
      except:
        print('Something did not work for:')
        print(f'{key}: {D[key]}')
        pass

  # --- atm namelist
  fpath_nml = df.loc[nn,'path_data']+'NAMELIST_'+df.loc[nn,'run']+'_atm'
  
  ### --- work around: f90nml has problems with the colon (:) in echam_sso_config(:)%gklift
  ###     so copy namelist file and replace this colon with 1
  # --- work around: f90nml has problems with structures indicated by %
  #     so copy namelist file and replace everything befor %
  if os.path.exists(fpath_nml):
    f = open(fpath_nml, 'r')
    #txt = f.read()
    lines = f.readlines()
    f.close()
    for kk in range(len(lines)):
      # delete lines with comments in namelist (line which starts with !)
      #lines[kk] = re.sub(' *!.*', '', lines[kk])
      # replace everything between echam_ and % 
      lines[kk] = re.sub('echam_.*%',' ',lines[kk])
    #txt2 = re.sub('echam_sso_config\(:\)','echam_sso_config(1)', txt)
    f = open('tmp_atm.nml', 'w')
    #f.write(txt2)
    f.writelines(lines)
    f.close()
  else:
    print(f'::: Warning: {fpath_nml} does not exist!:::')
    continue
  #print(f'nn = {nn}, run = {df.run[nn]}')
  #if df.run[nn]=='slo1235':
  #  print('halt stop')
  #  sys.exit()

  #try:
  if True:
    # ------ open namelist
    #nml = f90nml.read(fpath_nml)
    nml = f90nml.read('tmp_atm.nml')

    #print(f'nn = {nn}, run = {df.run[nn]}')
    #if df.run[nn]=='slo1235':
    #  print('halt stop')
    #  sys.exit()
    
    # ------ go through all sections (sub-namelists)
    D = dict()
    for nml_sec in nml.keys():
      if nml_sec=='output_nml':
        continue
      for entr in nml[nml_sec]:
        try:
          D[entr] = {nml[nml_sec][entr]}
        except:
          #print(f'xx  {entr}')
          pass
    
    # ------ add namelist values to pandoc data frame
    for key in D.keys():
      #print(f'{key}: {D[key]}')
      try:
        ll = list(D[key])
        if len(ll)==1:
          D[key] = ll[0]
        else:
          D[key] = ll
        if not key in df.columns.tolist():
          df[key] = np.nan
        df.loc[nn,key] = D[key]
      except:
        print('Something did not work for:')
        print(f'{key}: {D[key]}')
        pass

#df.to_csv("./out_gather_parameter.csv")
#sys.exit()

# --- reduce data
dfbcp = df.copy()

# --- delete simulations without parameters
df = df.dropna(how='all') 
dind = []
for nn in range(df.shape[0]):
  #print(nn)
  do_delete = df.iloc[nn,2:].isnull().all()
  if do_delete:
    print(f'drop row {nn}')
    dind.append(nn)
df = df.drop(dind, axis=0)
df = df.reset_index(drop=True)

## --- correct some parameters
for nn in range(df.shape[0]):
  if df.loc[nn,'gmredi_configuration']==0:
    df.loc[nn, 'k_tracer_gm_kappa_parameter'] = 0.
    df.loc[nn, 'k_tracer_isoneutral_parameter'] = 0.
df.loc[df['gkdrag'].isnull(), 'gkdrag'] = 0.05

# --- delete parameters which do not change for all simulations
dind = []
cols = df.columns.tolist()
for nn in range(df.shape[1]):
  if df.iloc[:,nn].unique().size==1:
    #print(f'{nn}: {df.columns[nn]}: {df.iloc[:,nn].unique()}')
    dind.append(cols[nn])
  elif df.iloc[:,nn].unique().size==2:
    #print(f'{df.columns[nn]}: {df.iloc[:,nn].unique()}')
    dind.append(cols[nn])
    #pass
  else:
    print(f'{nn}: {df.columns[nn]}: {df.iloc[:,nn].unique()}')
df = df.drop(dind, axis=1)
df['tave_int'] = ['none']*df.shape[0]

# --- add links to names
df['qps'] = ['none']*df.shape[0]
key = 'run'
#key = '0 Exp.Name'
if True:
  print('Waiting for url assignment...')
  # --- check differen possible urls
  web_str1 = 'https://modvis.dkrz.de/mh0469/m211032/pyicon/qp-NAME/qp_index.html'
  web_str2 = 'https://modvis.dkrz.de/mh0469/m300466/pyicon/all_qps/index.html'
  web_str3 = 'https://modvis.dkrz.de/mh0287/m211054/all_qps/index.html'
  for nn in range(len(df[key])):
    print(df[key][nn])
    url1 = web_str1.replace('NAME', df[key][nn])
    url2 = web_str2.replace('NAME', df[key][nn])
    url3 = web_str3.replace('NAME', df[key][nn])
    if check_url(url1):
      url = url1
    elif check_url(url2):
      url = url2
    elif check_url(url3):
      url = url3
    else:
      url = 'none'
    # --- if url was found replace long url name by simply 'qps' but contain link
    if url!='none':
      url = f"[qps]({url})"
    df.loc[nn,'qps'] = url
  print('Done assigning urls.')
else:
  # the following list can be obtained by executing this script with the above if==True
  # and then executing the following lines
  # for nn in range(df.shape[0]):
  #   print(f"df.loc[{nn},'url'] = '{df.loc[nn, 'url']}'")
  pass

# --- sort some columns
first_cols = ['run', 'qps', 'tave_int']
cols = df.columns.tolist()
for col in first_cols: 
  cols = list(filter(lambda a: a != col, cols)) 
cols = first_cols + cols
df = df[cols]

# --- sort rows
df = df.sort_values(by='run')

# --- delet some cols
df = df.drop(columns=[
  #'path_data', 
  'restart_filename', 
  'output_nml_dict', 'netcdf_dict',
])

# --- add results
for nn in range(df.shape[0]):
  path_data = df.loc[nn,'path_data']
  if not isinstance(path_data, str): #np.isnan(path_data):
    continue
  print(f'nn = {nn}/{df.shape[0]};  {path_data}')
  run = df.loc[nn,'run']

  # --- ocean monitoring
  flist = glob.glob(path_data+run+'_oce_mon_*.nc')
  flist.sort()
  #if len(flist)==0:
  #  continue
  #elif len(flist)>1:
  #  fpath = flist[-2]
  #else:
  #  fpath = flist[-1]
  if len(flist)<5:
    print(f'Too little data for {path_data}')
  else:
     fpath = flist[-5:-1]
     for fp in fpath:
       print(fp.split('/')[-1])
  df.loc[nn, 'tave_int'] = (   
      fpath[0].split('/')[-1].split('_')[-1].split('.')[0][:4]
    + ' - ' 
    + fpath[-1].split('/')[-1].split('_')[-1].split('.')[0][:4])
  #df.loc[nn, 'file'] = fpath.split('/')[-1]
  #print(f"{df.loc[nn, 'run']}: {df.loc[nn, 'file']}")
  #ds = xr.open_dataset(fpath, decode_times=False)
  #ds = ds.mean(dim='time')
  dmallxr = xr.DataArray(np.tile(np.array([31,28,31,30,31,30,31,31,30,31,30,31]), (10*len(fpath))), dims=['time'])
  ds = xr.open_mfdataset(fpath, decode_times=False, combine='by_coords')
  if ds.time.size!=120*len(fpath):
    print(f'Unappropriate dimension {ds.time.size}')
    print(fpath)
    continue
  ds = ((ds*dmallxr).sum(dim='time')/dmallxr.sum(dim='time')).compute()
  for kk, var in enumerate(ds):
    if not var in df.columns.tolist():
      df[var] = np.nan
    df.loc[nn, var] = ds[var].data[0][0] 

  # --- atmosphere monitoring
  flist = glob.glob(path_data+run+'_atm_mon_*.nc')
  flist.sort()
  #if len(flist)==0:
  #  continue
  #elif len(flist)>1:
  #  fpath = flist[-2]
  #else:
  #  fpath = flist[-1]
  if len(flist)<5:
    print(f'Too little data for {path_data}')
  else:
     fpath = flist[-5:-1]
     for fp in fpath:
       print(fp.split('/')[-1])
  #ds = xr.open_dataset(fpath, decode_times=False)
  #ds = ds.mean(dim='time')
  dmallxr = xr.DataArray(np.tile(np.array([31,28,31,30,31,30,31,31,30,31,30,31]), (10*len(fpath))), dims=['time'])
  try:
    ds = xr.open_mfdataset(fpath, decode_times=False, combine='by_coords')
    ds = ((ds*dmallxr).sum(dim='time')/dmallxr.sum(dim='time')).compute()
    ds['tas_gmean'] += -273.15
    for kk, var in enumerate(ds):
      if not var in df.columns.tolist():
        df[var] = np.nan
      df.loc[nn, var] = ds[var].data[0][0] 
  except:
    print(f'There was a problem with {path_data}!')
    print(fpath)

# --- reduce digits
for col in df.columns.tolist():
  try:
    df[col] = df[col].map('{:.4g}'.format)
  except:
    pass

#fpath = "./out_gather_parameter_new.csv"
fpath = f"../csv/ruby0_db_v003.csv"
print(f'Writing file {fpath}')
df.to_csv(fpath)


