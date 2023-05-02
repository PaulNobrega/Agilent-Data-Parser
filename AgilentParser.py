import os
import struct
import glob
import numpy as np
from parse import *

def read_agilent_d_file(d_folder):
    '''
        Method reads in native agilent *.D/*.CH files.
        Data on the agilent appears 10x higher in amplitude than the raw reads from CH files.
        Check your instrument and adjust as necessary.
        Correction Scalar is applied here.
    '''
    correction_scalar = 0.1
    
    try:
        fname = [f for f in glob.glob(d_folder + "**/*.ch", recursive=False)][0]
        xml_list = [f for f in glob.glob(d_folder + "**/*SAMPLE.XML", recursive=False)]
        xmlname = [f for f in glob.glob(d_folder + "**/*SAMPLE.XML", recursive=False)] if len(xml_list) > 0 else None
    except Exception as e:
        print(str(e))
        return False

    f = open(fname, 'rb')
    f.seek(0x1075)
    sig_name = f.read(2 * struct.unpack('>B', f.read(1))[0]).decode('utf-16')

    # wavelength the file was collected at
    wv = sig_name.split('=')[1].split()[0].split(',')[0]

    f.seek(0x127C)
    del_ab = struct.unpack('>d', f.read(8))[0]

    # get y values
    data = []
    f.seek(0x1800)
    while True:
        x, nrecs = struct.unpack('>BB', f.read(2))
        if x == 0 and nrecs == 0:
            break
        for _ in range(nrecs):
            inp = struct.unpack('>h', f.read(2))[0]
            if inp == -32768:
                inp = struct.unpack('>i', f.read(4))[0]
                data.append(del_ab * inp)
            elif len(data) == 0:
                data.append(del_ab * inp)
            else:
                data.append(data[-1] + del_ab * inp)
    f.close()

    # correct data with scalar
    data = list(np.array(data) * correction_scalar)

    # get start and end times
    f = open(fname, 'rb')
    f.seek(0x11A)
    st_t = struct.unpack('>i', f.read(4))[0] / 60000.
    en_t = struct.unpack('>i', f.read(4))[0] / 60000.
    f.close()

    # construct time axis
    times = np.linspace(st_t, en_t, len(data))

    # read SAMPLE.XML -- Some versions of chemstation do not produce this file
    protein = None
    amount = None
    multiplier = None
    dilution = None
    description = None
    if xmlname is not None:
        xmlTree = parse(xmlname)
        # Get protein name/attributes
        protein = xmlTree.find('Name').text
        amount = xmlTree.find('Amount').text
        multiplier = xmlTree.find('Multiplier').text
        dilution = xmlTree.find('Dilution').text
        description = xmlTree.find('Description').text

    return {'d_file_name': os.path.dirname(fname), 'wavelength': wv,'raw_data': {'x': times, 'y':data}, 'xml_data': {'sample_name': protein, 'sample_amount': amount, 'multiplier':multiplier, 'dilution_factor':dilution, 'sample_description':description},}


def write_txt(parsed_data_dict, output_file_name):
    with open(os.path.join(experiment_folder_name, os.path.basename(output_file_name)), 'w') as f:
        # write header
        f.write(f'Time(min)\tAbs[{parsed_data_dict["wavelength"]}nm] (arb.units)\tsample name\tsample amount\tdilution factor\tdescription\n')
        # set values
        x_val = parsed_data_dict['raw_data']['x']
        y_val = parsed_data_dict['raw_data']['y']
        sample_name = str(parsed_data_dict['xml_data']['sample_name'])
        sample_amount = str(parsed_data_dict['xml_data']['sample_amount'])
        dilution_factor = str(parsed_data_dict['xml_data']['dilution_factor'])
        description = str(parsed_data_dict['xml_data']['sample_description'])
        # write values
        for i in range(len(x_val)):
            if i == 0:
                f.write(f'{x_val[i]}\t{y_val[i]}\t{sample_name}\t{sample_amount}\t{dilution_factor}\t{description}\n')
            else:
                f.write(f'{x_val[i]}\t{y_val[i]}\n')
    return


if __name__ == "__main__":
    experiment_folder_name = r'PATH_TO_EXPERIMENT_DIRECTORY_CONTAINING_.D_SUBDIRECTORIES'
    all_D_folders = glob.glob(experiment_folder_name + "**/*.D", recursive=False)
    for d in all_D_folders:
        parsed_data_dict = read_agilent_d_file(d)
        output_file_name = f'{parsed_data_dict["d_file_name"]}.txt'
        write_txt(parsed_data_dict, output_file_name)
