# -*- coding: utf-8 -*-
"""
Created on Fri Sep 10 16:24:47 2021

@author: bagus
"""

import cfgrib
from netCDF4 import Dataset
import requests
import os

print('Masukkan Tanggal (yymmdd)')
print('(contoh: 20210909 atau 20210908,20210909 jika lebih dari satu)')
list_tanggal = [str(x) for x in input().split(',')]

def download(tanggal):
    list_jam = ['00','06','12']
    folder = 'C:/CircleGeo/GRIB/' + tanggal
    
    for jam in list_jam:
        dest_folder = folder + '/' + jam
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
        for i in range(0, 49):
            waktu_f = str(i).zfill(2)
            path = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t{}z.pgrb2.0p25.f0{}&lev_1000_mb=on&lev_500_mb=on&lev_800_mb=on&lev_surface=on&var_APCP=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=70&rightlon=170&toplat=40&bottomlat=-25&dir=%2Fgfs.{}%2F{}%2Fatmos'.format(jam,waktu_f,tanggal,jam)
            response = requests.get(path, allow_redirects = True)
            filename = 'gfs.t{}z.pgrb2.0p25.f0{}.grib2'.format(jam,waktu_f)
            open(dest_folder + '/' + filename,'wb').write(response.content)

def buat_nc(tanggal):
    list_jam = ['00']
    folder_grib = 'C:/CircleGeo/GRIB/' + tanggal
    folder_nc = 'C:/CircleGeo/NC/' + tanggal
    tggl_rapi = "{}-{}-{}".format(str(tanggal)[:4],(tanggal)[4:6],(tanggal)[6:])
    
    for jam in list_jam:
        src_folder_grib = folder_grib + '/' + jam
        src_folder_nc = folder_nc + '/' + jam
        
        #Membuat file NC
        fn = 'C:/CircleGeo/{}-{}.nc'.format(tanggal,jam)
        data_nc = Dataset(fn, 'w', format='NETCDF4')
        
        #Deklarasi dimensi
        time = data_nc.createDimension('time', None)
        lat = data_nc.createDimension('lat', 261)
        lon = data_nc.createDimension('lon', 401)
        level = data_nc.createDimension('level', 13)
        
        #deklarasi variabel
        times = data_nc.createVariable('time', 'f4', ('time',))
        lats = data_nc.createVariable('lat', 'f4', ('lat',))
        lons = data_nc.createVariable('lon', 'f4', ('lon',))
        levels = data_nc.createVariable('level', 'f4', ('level',))
        rr = data_nc.createVariable('rr', 'f4', ('time','lat','lon',))
        tp24 = data_nc.createVariable('tp24', 'f4', ('time','lat','lon',))
        u_val = data_nc.createVariable('u', 'f4', ('time','level','lat','lon',))
        v_val = data_nc.createVariable('v', 'f4', ('time','level','lat','lon',))
        
        #deklarasi units
        times.units = 'minutes since {} 00:00'.format(tggl_rapi)
        lats.units = 'degrees_north'
        lons.units = 'degrees east'
        levels.units ='mbar'
        rr.units ='mm/hour'
        tp24.units ='mm/day'
        u_val.units ='knot'
        v_val.units ='knot'
        
        #deklarasi long_name
        lons.long_name = 'Longitude'
        lats.long_name = 'Latitude'
        levels.long_name = 'isobaric level'
        rr.long_name = 'Rain Rate'
        tp24.long_name = 'Total precipitation in 24 Hours'
        u_val.long_name = 'U component of wind'
        v_val.long_name ='V component of wind'
        
        #Deklarasi FillValue
        rr.FillValue = '-9.99e+08f'
        tp24.FillValue = '-9.99e+08f'
        u_val.FillValue = '-9.99e+08f'
        v_val.FillValue = '-9.99e+08f'
         
        for i in range(0,49):
            waktu_f = str(i).zfill(2)
            path_grib = src_folder_grib + '/' + 'gfs.t00z.pgrb2.0p25.f0{}.grib2'.format(waktu_f)
            path_nc = src_folder_nc + '/' + 'gfs.t00z.pgrb2.0p25.f0{}.nc'.format(waktu_f)
            #Membaca GRIB dan Convert ke NC
            ds = cfgrib.open_dataset(path_grib)
            ds.to_netcdf(path_nc)

            #Membuka NC dan Membaca Variabel
            data = Dataset(path_nc,'r')
            lat_nc = data.variables['latitude'][:] #variabel latitude
            lon_nc = data.variables['longitude'][:] #variabel longitude
            u_nc = data.variables['u'][:] #variabel u
            v_nc = data.variables['v'][:] #variabel v
            tanggal_nc = data.variables['time'][:] #detik sejak 1970-01-01 00:00:00 ke tanggal data (hari)
            jam_nc = data.variables['valid_time'][:] #detik sejak 1970-01-01 00:00:00 ke tanggal dan waktu data
            level_nc = data.variables['isobaricInhPa'][:] #variabel level (1 hPa = 1 mbar)

            #Membaca variabel hujan, pada f000 tidak ditemukan variabel hujan
            list_variables = []
            for variables in data.variables.keys():
                list_variables.append(variables)
            if 'tp' in list_variables:
                hujan = data.variables['tp'][:] #variabel hujan (1 kg/m2 = 1 mm dari hujan)
                hujan_hari = hujan * 24 #mm/hr ke mm/day

            #Mengubah satuan angin dari m/s ke knot (dikali 1.94)
            u_knot = u_nc * 1.94
            v_knot = v_nc * 1.94
            
            #Mendapatkan Variabel Waktu dalam menit sejak 2021-09-06 00:00
            new_time = int((jam_nc[()] - tanggal_nc[()])/60)
            
            #Membuat NC
            lons = lon_nc
            lats = lat_nc
            times[i] = new_time
            levels = level_nc
            if 'tp' in list_variables:
                rr[i,:,:] = hujan[:,:]
                tp24[i,:,:] = hujan_hari[:,:]
            for lv in level_nc:
                for j in range(0,3):
                    u_val[i,j,:,:] = u_knot[j,:,:]
                    v_val[i,j,:,:] = v_knot[j,:,:]
    ds.close()
    data_nc.close()
            
for tanggal in list_tanggal:
    download(tanggal)
    buat_nc(tanggal)
            



