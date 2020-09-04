import os
import pandas as pd
import shapely 
import dateutil 
from owslib.wps import WebProcessingService
from datetime import datetime, timedelta
import geopandas as gpd
import cioppy
from shapely.wkt import loads
from urlparse import urlparse
import gdal 
import numpy as np

def analyse(row, aoi):

    aoi_intersection = (row.geometry.intersection(aoi).area / aoi.area) * 100

    series = dict([('aoi_intersection', aoi_intersection)])

    return pd.Series(series)


def analyse_post_acquisitions(row, pre_acquisition, aoi):

    pre_acquisition_wkt = pre_acquisition.geometry
    pre_acquisition_date = dateutil.parser.parse(pre_acquisition.startdate)

    pre_acquisition_coverage = (row.geometry.intersection(pre_acquisition_wkt).area / pre_acquisition_wkt.area) * 100
    aoi_intersection = (row.geometry.intersection(aoi).area / aoi.area) * 100
    temporal_baseline = round(divmod((pre_acquisition_date - dateutil.parser.parse(row.startdate)).total_seconds(), 3600 * 24)[0] +
                              round(divmod((pre_acquisition_date - dateutil.parser.parse(row.startdate)).total_seconds(), 3600 * 24)[1])/(3600 * 24))

    series = dict([('pre_acquisition_coverage', pre_acquisition_coverage),
                  ('aoi_intersection', aoi_intersection),
                  ('temporal_baseline', temporal_baseline)])

    return pd.Series(series)


def get_parameters_as_dict(wps_url, process_id):
    """This function returns a dictionary with the WPS parameters and their associated default values

    Args:
        wps_url: the WPS end-point.
        process_id: the process identifier

    Returns
        A dictionary with the parameters as keys .

    Raises:
        None.
    """
    wps = WebProcessingService(wps_url, verbose=False, skip_caps=True)

    process = wps.describeprocess(process_id)

    data_inputs = dict()

    for data_input in process.dataInputs:
        # TRIGGER-15
        if data_input.identifier == '_T2Username' or data_input.identifier == '_T2ApiKey': continue

        if (data_input.minOccurs != 0) or (data_input.identifier == 't2_coordinator_name') or (data_input.identifier == '_T2Username'):
            if data_input.defaultValue is None:
                data_inputs[data_input.identifier] = ''
            else:
                data_inputs[data_input.identifier] = data_input.defaultValue

    return data_inputs

def get_vsi_url(enclosure, username, api_key):
    
    
    parsed_url = urlparse(enclosure)

    url = '/vsicurl/{}://{}:{}@{}/api{}'.format(list(parsed_url)[0],
                                            username, 
                                            api_key, 
                                            list(parsed_url)[1],
                                            list(parsed_url)[2])
    
    return url 


def vsi_download(row, bbox, username, api_key):
    
    vsi_url = get_vsi_url(row.enclosure, username, api_key)
    
    ulx, uly, lrx, lry = bbox[0], bbox[3], bbox[2], bbox[1] 
    
    # load VSI URL in memory
    output = '/vsimem/subset.tif'
    
    ds = gdal.Open(vsi_url)
    
    ds = gdal.Translate(destName=output, 
                        srcDS=ds, 
                        projWin = [ulx, uly, lrx, lry], 
                        projWinSRS = 'EPSG:4326',
                        outputType=gdal.GDT_Float32)
    ds = None
    
    # create a numpy array
    ds = gdal.Open(output)
    
    layers = []

    for i in range(1, ds.RasterCount+1):
        layers.append(ds.GetRasterBand(i).ReadAsArray())

    return np.dstack(layers)



def get_master(row, time_delta):

    series = 'https://catalog.terradue.com/sentinel1/search'

    master_search_params = dict([('geom', row.geometry.wkt),
                             ('track', row.track),
                             ('pt', row.productType),
                             ('psn', row.platform),
                             ('start', datetime.strftime((dateutil.parser.parse(row.startdate) + timedelta(days=-12 + time_delta)), '%Y-%m-%dT%H:%M:%SZ')),
                             ('stop', datetime.strftime((dateutil.parser.parse(row.startdate) + timedelta(days=-1 + time_delta)), '%Y-%m-%dT%H:%M:%SZ')),
                             ('do', 'terradue')])


    master_search = gpd.GeoDataFrame(cioppy.Cioppy().search(end_point=series,
                                           params=master_search_params,
                                           output_fields='self,productType,track,enclosure,identifier,wkt,startdate,platform',
                                           model='EOP',
                                                   timeout=50000))

    master_search['geometry'] = master_search['wkt'].apply(loads)
    master_search = master_search.drop(columns=['wkt'])

    master_search = master_search.merge(master_search.apply(lambda row_master: analyse(row_master, row.geometry), axis=1),
              left_index=True,
              right_index=True)


    best_master = master_search[master_search.aoi_intersection == master_search.aoi_intersection.max()].iloc[0]

    #print(type(best_master))

    #print(best_master)
    series = dict()

    series['master_self'] = best_master.self
    series['master_track'] = best_master.track
    series['master_startdate'] = best_master.startdate
    series['master_platform'] = best_master.platform
    series['master_identifier'] = best_master.identifier

    return pd.Series(series)


def check_status(row, creds):

    ciop = cioppy.Cioppy()

    search = ciop.search(end_point=row.self,
                params=[],
                output_fields='self,cat,link:results',
                model='GeoTime',
                creds=creds)[0]

    series = dict()

    series['status'] = filter(lambda element: 'source' in element, search['cat'].split(';'))[0]
    series['link_results'] = search['link:results']

    return pd.Series(series)