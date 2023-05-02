# Agilent-Data-Parser
Python code example to directly parse binary *.D files produced by Agilent Chemstation software


#Use this Example
1. pip install -r requirements.txt
2. edit varibale 'experiment_folder_name' in main entry point to reflect the correct location fo the chemstation experiment file
```
if __name__ == "__main__":
    experiment_folder_name = r'PATH'  # <---edit this line
    all_D_folders = glob.glob(experiment_folder_name + "**/*.D", recursive=False)
    for d in all_D_folders:
        print(f"opening folder: {d}")
        parsed_data_dict = read_agilent_d_file(d)
        output_file_name = f'{parsed_data_dict["d_file_name"]}.txt'
        write_txt(parsed_data_dict, output_file_name)
```
3. execute
