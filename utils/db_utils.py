import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import numpy as np


def update_dataframe(csv_path, new_dataframe):
    """
    Load a Pandas dataframe CSV if it exists, update it given a new dataframe by adding the rows of the new dataframe
    (check that the column names match), and return a new combined dataframe. Avoids adding duplicate rows.
    """
    # check if CSV file exists
    if os.path.exists(csv_path):
        # load existing dataframe
        existing_dataframe = pd.read_csv(csv_path)

        # check if column names match
        if set(existing_dataframe.columns) == set(new_dataframe.columns):
            # drop duplicates from new dataframe
            new_dataframe = new_dataframe.drop_duplicates()

            # concatenate dataframes and drop duplicates
            combined_dataframe = pd.concat([existing_dataframe, new_dataframe], ignore_index=True)
            combined_dataframe = combined_dataframe.drop_duplicates()

            return combined_dataframe
        else:
            print("Column names do not match.")
    else:
        # CSV file does not exist, return new dataframe
        return new_dataframe


def update_ndarray(npy_path, new_ndarray):
    """
    Load a float32 NumPy ndarray if it exists, update it given a new ndarray by adding the rows of the new ndarray
    (check that the shape matches), and return a new combined ndarray. Avoids adding duplicate rows.
    """
    # check if NPY file exists
    if os.path.exists(npy_path):
        # load existing ndarray
        existing_ndarray = np.load(npy_path)

        # check if shapes match
        if existing_ndarray.shape[1:] == new_ndarray.shape[1:]:
            # concatenate ndarrays
            combined_ndarray = np.vstack((existing_ndarray, new_ndarray))

            # remove duplicate rows
            unique_rows = np.unique(combined_ndarray, axis=0)

            return unique_rows.astype(np.float32)
        else:
            print("Shapes do not match.")
    else:
        # NPY file does not exist, return new ndarray
        return new_ndarray.astype(np.float32)


def update_txt(txt_path, new_lines):
    """
    Load a text file if it exists, update it given new lines by appending them to the end of the file,
    and return a list of all lines in the file (without duplicates).
    """
    # check if TXT file exists
    if os.path.exists(txt_path):
        # load existing lines
        with open(txt_path, "r") as f:
            existing_lines = f.read().splitlines()

        # concatenate new lines to existing lines
        all_lines = existing_lines + new_lines

        # remove duplicate lines
        unique_lines = list(set(all_lines))

        # write unique lines to file
        with open(txt_path, "w") as f:
            f.write("\n".join(unique_lines))

        return unique_lines
    else:
        # TXT file does not exist, create new file
        with open(txt_path, "w") as f:
            f.write("\n".join(new_lines))

        return new_lines


def delete_files_except_extensions(directory_path, extensions_list):
    """Delete all files and folders from a directory except those whose extension is in the specified list."""
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_extension = os.path.splitext(file_path)[1]
            if file_extension not in extensions_list:
                os.remove(file_path)
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)


def get_filenames_with_extensions(directory, extensions_list):
    """Get the filenames of all files with specified extensions in a directory."""
    all_files = os.listdir(directory)
    filtered_files = [file for file in all_files if os.path.splitext(file)[1].lower() in extensions_list]
    return filtered_files
