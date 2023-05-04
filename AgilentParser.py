import os
import struct
import glob
import numpy as np
from parse import *
import PyPDF2

def read_agilent_d_file(d_folder):
    '''
        Method reads in native agilent *.D/*.CH files.
        Data on the agilent appears 10x higher in amplitude than the raw reads from CH files.
        Correction Scalar is applied here.
    '''

    # Set Scalar Variable
    correction_scalar = 0.1

    # define private methods...
    def _get_files(d_folder):
        '''Get files from within .D folder for data parsing procedures'''
        try:
            ch_name = [f for f in glob.glob(d_folder + "**/*.ch", recursive=False)][0]
            xml_list = [f for f in glob.glob(d_folder + "**/*SAMPLE.XML", recursive=False)]
            xml_name = xml_list[0] if len(xml_list) > 0 else None
            pdf_list = [f for f in glob.glob(d_folder + "**/*.PDF", recursive=False)]
            pdf_name = pdf_list[0] if len(pdf_list) > 0 else None
            return ch_name, xml_name, pdf_name
        except Exception as e:
            print(str(e))
            return False

    def _parse_ch_file(ch_file, correction_scalar):
        ''' Parse Agilent .CH file to return XY coordinate vectors and acquisition wavelength'''
        f = open(ch_file, 'rb')
        f.seek(0x1075)
        sig_name = f.read(2 * struct.unpack('>B', f.read(1))[0]).decode('utf-16')

        # wavelength the file was collected at
        wavelength = sig_name.split('=')[1].split()[0]
        wavelength = wavelength.split(',')[0] if ',' in wavelength else wavelength

        f.seek(0x127C)
        del_ab = struct.unpack('>d', f.read(8))[0]

        # get y values
        y_data = []
        f.seek(0x1800)
        while True:
            x, nrecs = struct.unpack('>BB', f.read(2))
            if x == 0 and nrecs == 0:
                break
            for _ in range(nrecs):
                inp = struct.unpack('>h', f.read(2))[0]
                if inp == -32768:
                    inp = struct.unpack('>i', f.read(4))[0]
                    y_data.append(del_ab * inp)
                elif len(y_data) == 0:
                    y_data.append(del_ab * inp)
                else:
                    y_data.append(y_data[-1] + del_ab * inp)
        f.close()

        # correct data with scalar
        data = list(np.array(y_data) * correction_scalar)

        # get start and end times
        f = open(ch_file, 'rb')
        f.seek(0x11A)
        st_t = struct.unpack('>i', f.read(4))[0] / 60000.
        en_t = struct.unpack('>i', f.read(4))[0] / 60000.
        f.close()

        # construct time axis
        x_data = np.linspace(st_t, en_t, len(y_data))


        return x_data, y_data, wavelength
    
    def _parse_xml_file(xml_file):
        '''Parse Sample.xml file and construct dictionary of sample information'''
        # Some versions/settings of chemstation do not produce this file
        if xml_file is None:
            return {}
        
        # Get protein name/attributes
        xmlTree = parse(xml_file)
        sample_name = xmlTree.find('Name').text
        amount = xmlTree.find('Amount').text
        multiplier = xmlTree.find('Multiplier').text
        dilution = xmlTree.find('Dilution').text
        description = xmlTree.find('Description').text
        xml_data_dict = {'sample_name': sample_name, 'sample_amount': amount, 'multiplier':multiplier, 'dilution_factor':dilution, 'sample_description':description}
        return xml_data_dict
        
    def _parse_pdf_file(pdf_file):
        '''Parse .pdf file and construct dictionary of sample information'''
        # Some versions/settings of chemstation do not produce this file
        if pdf_file is None:
            return {}
        
        # Get protein name/attributes
        pdf = PyPDF2.PdfReader(pdf_file)
        text = pdf.pages[0].extract_text().split('\n')
        
        for line in text:
            if 'Multiplier' in line:
                multiplier = line.split(':')[-1].strip()
            elif 'Dilution' in line:
                dilution = line.split(':')[-1].strip()
            elif 'Sample Name' in line:
                sample_name = line.split(':')[-1].strip()
            elif 'Actual Inj Volume' in line:
                amount = line.split(':')[-1].strip()
            elif 'Method Info' in line:
                description = line.split(':')[-1].strip()

        pdf_data_dict = {'sample_name': sample_name, 'sample_amount': amount, 'multiplier':multiplier, 'dilution_factor':dilution, 'sample_description':description}
        return pdf_data_dict

    #  Method Entry Point
    ch_file, xml_file, pdf_file = _get_files(d_folder)
    x_data, y_data, wavelength = _parse_ch_file(ch_file, correction_scalar)
    xml_data_dict = _parse_xml_file(xml_file)
    pdf_data_dict = _parse_pdf_file(pdf_file)
    sample_data_dict = xml_data_dict if xml_data_dict != {} else pdf_data_dict
    return {'d_file_name': os.path.dirname(ch_file), 'wavelength': wavelength,'raw_data': {'x': x_data, 'y':y_data}, 'sample_data': sample_data_dict,}

    

def write_txt(parsed_data_dict, output_file_name):
    with open(os.path.join(experiment_folder_name, os.path.basename(output_file_name)), 'w') as f:
        # write header
        f.write(f'Time(min)\tAbs[{parsed_data_dict["wavelength"]}nm] (mAU)\tsample name\tsample amount\tdilution factor\tdescription\n')
        # set values
        x_val = parsed_data_dict['raw_data']['x']
        y_val = parsed_data_dict['raw_data']['y']
        sample_name = str(parsed_data_dict['sample_data']['sample_name'])
        sample_amount = str(parsed_data_dict['sample_data']['sample_amount'])
        dilution_factor = str(parsed_data_dict['sample_data']['dilution_factor'])
        description = str(parsed_data_dict['sample_data']['sample_description'])
        # write values
        for i in range(len(x_val)):
            if i == 0:
                f.write(f'{x_val[i]}\t{y_val[i]}\t{sample_name}\t{sample_amount}\t{dilution_factor}\t{description}\n')
            else:
                f.write(f'{x_val[i]}\t{y_val[i]}\n')
    return


# Main entry point
if __name__ == "__main__":
    experiment_folder_name = r'PATH_TO_EXPERIMENT_DIRECTORY_CONTAINING_.D_SUBDIRECTORIES'
    all_D_folders = glob.glob(experiment_folder_name + "/*.D", recursive=False)
    for d in all_D_folders:
        print(f"opening folder: {d}")
        parsed_data_dict = read_agilent_d_file(d)
        output_file_name = f'{parsed_data_dict["d_file_name"]}_exported.txt'
        write_txt(parsed_data_dict, output_file_name)
