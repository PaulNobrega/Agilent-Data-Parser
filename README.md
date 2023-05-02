# Agilent-Data-Parser
Python code example to directly parse binary *.D files produced by Agilent Chemstation software


## Use this Example
1. pip install -r requirements.txt
2. edit varibale 'experiment_folder_name' in main entry point to reflect the correct location fo the chemstation experiment file

***AgilentParser.py***
```python
if __name__ == "__main__":
    experiment_folder_name = r'PATH_TO_EXPERIMENT_DIRECTORY_CONTAINING_.D_SUBDIRECTORIES'  # <---edit this line
    all_D_folders = glob.glob(experiment_folder_name + "**/*.D", recursive=False)
    for d in all_D_folders:
        ...
```
3. execute
