#!/usr/bin/env python
# coding: utf-8
"""Extract data from spreadsheets and write to an OSeMOSYS datafile

"""
import csv
import logging
import os
import sys

import xlrd

logger = logging.getLogger(__name__)


def generate_csv_from_excel(input_workbook, output_folder):
    """Generate a folder of CSV files from a spreadsheet

    Arguments
    ---------
    input_workbook : str
        Path to spreadsheet containing OSeMOSYS data
    output_folder : str
        Path of the folder containing the csv files

    """
    work_book = xlrd.open_workbook(os.path.join(input_workbook))

    _csv_from_excel(work_book, output_folder)
    work_book.release_resources()  # release the workbook-resources
    del work_book


def write_datafile(output_folder, output_file):
    """Create an OSeMOSYS datafile from a folder of CSV files

    Arguments
    ---------
    output_folder : str
        Path of the folder containing the csv files
    output_file
        Path to datafile to be written
    """
    sheet_names = [x.strip(".csv") for x in os.listdir(output_folder)]

    sorted_names = sorted(sheet_names)

    fileOutput = _parseCSVFilesAndConvert(sorted_names, output_folder)
    with open(output_file, "w") as text_file:
        text_file.write(fileOutput)
        text_file.write("end;\n")


def main(input_workbook, output_file, output_folder):
    """Creates a model file from an Excel workbook containing OSeMOSYS data

    Arguments
    ---------
    input_workbook : str
        Path to spreadsheet containing OSeMOSYS data
    output_file
        Path to datafile to be written
    output_folder : str
        Path of the folder containing the csv files

    """
    generate_csv_from_excel(input_workbook, output_folder)
    write_datafile(output_folder, output_file)


def _csv_from_excel(workbook, output_folder):
    """Creates csv files from all sheets in a workbook

    Arguments
    ---------
    workbook :
    output_folder : str
    """

    logger.debug("Generating CSVs from Excel %s", workbook)
    # Create all the csv files in a new folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)  # creates the csv folder

    # Iterate over each sheet in the workbook
    for sheet in workbook.sheets():  # typing: xlrd.book.Sheet

        name = sheet.name
        mod_name = _modify_names([name])

        # Open the sheet name in the xlsx file and write it in csv format]
        filepath = os.path.join(output_folder, mod_name[0] + '.csv')
        with open(filepath, 'w', newline='') as your_csv_file:
            wr = csv.writer(your_csv_file, quoting=csv.QUOTE_NONNUMERIC)

            for rownum in range(sheet.nrows):  # reads each row in the csv file
                row = _cast_to_integer(sheet.row_values(rownum))
                wr.writerow(row)


def _cast_to_integer(row):
    """function to convert all float numbers to integers....need to check it!!
    """
    if all(isinstance(n, float) for n in row):
        converted_row = list(map(int, row))
    else:
        converted_row = row
    return converted_row


def read_file_into_memory(sheet_name, output_folder):
    filepath = os.path.join(output_folder, sheet_name + '.csv')
    with open(filepath, 'r') as csvfile:
        reader = csv.reader(csvfile)
        return list(reader)


def _parseCSVFilesAndConvert(sheet_names, output_folder):
    """Holds the logic for writing out model entities in a certain format
    """
    result = ''
    for sheet_name in sheet_names:

        contents = read_file_into_memory(sheet_name, output_folder)

        # all the sets
        if (sheet_name in ['DAYTYPE', 'DAILYTIMEBRACKET', 'STORAGE', 'EMISSION',
                           'MODE_OF_OPERATION', 'REGION', 'FUEL', 'TIMESLICE',
                           'SEASON', 'TECHNOLOGY', 'YEAR']):
            result += 'set ' + sheet_name + ' := '
            for row in contents:
                result += " ".join(row) + " "
            result += ";\n"
        # all the parameters that have one variable
        elif (sheet_name in ['AccumulatedAnnualDemand', 'CapitalCost',
                             'CapitalCostStorage',
                             'FixedCost', 'ResidualCapacity',
                             'SpecifiedAnnualDemand',
                             'TotalAnnualMinCapacity',
                             'TotalAnnualMinCapacityInvestment',
                             'TotalTechnologyAnnualActivityLowerLimit']):
            result += 'param ' + sheet_name + ' default 0 := '
            result += '\n[SIMPLICITY, *, *]:\n'
            result += _insert_table(sheet_name, contents)
        # all the parameters that have one variable
        elif (sheet_name in ['TotalAnnualMaxCapacityInvestment']):
            result += 'param ' + sheet_name + ' default 99999 := '
            result += '\n[SIMPLICITY, *, *]:\n'
            result += _insert_table(sheet_name, contents)
        elif (sheet_name in ['AvailabilityFactor']):
            result += 'param ' + sheet_name + ' default 1 := '
            result += '\n[SIMPLICITY, *, *]:\n'
            result += _insert_table(sheet_name, contents)
        elif (sheet_name in ['TotalAnnualMaxCapacity',
                             'TotalTechnologyAnnualActivityUpperLimit']):
            result += 'param ' + sheet_name + ' default 9999999 := '
            result += '\n[SIMPLICITY, *, *]:\n'
            result += _insert_table(sheet_name, contents)
        elif (sheet_name in ['AnnualEmissionLimit']):
            result += 'param ' + sheet_name + ' default 99999 := '
            result += '\n[SIMPLICITY, *, *]:\n'
            result += _insert_table(sheet_name, contents)
        elif (sheet_name in ['YearSplit']):
            result += 'param ' + sheet_name + ' default 0 :\n'
            result += _insert_table(sheet_name, contents)
        elif (sheet_name in ['CapacityOfOneTechnologyUnit',
                             'EmissionsPenalty', 'REMinProductionTarget',
                             'RETagFuel', 'RETagTechnology',
                             'ReserveMargin', 'ReserveMarginTagFuel',
                             'ReserveMarginTagTechnology', 'TradeRoute']):
            result += 'param ' + sheet_name + ' default 0 := ;\n'
        # all the parameters that have 2 variables
        elif (sheet_name in ['SpecifiedDemandProfile']):
            result += 'param ' + sheet_name + ' default 0 := \n'
            result += _insert_two_variables(sheet_name, contents)
        # all the parameters that have 2 variables
        elif (sheet_name in ['VariableCost']):
            result += 'param ' + sheet_name + ' default 9999999 := \n'
            result += _insert_two_variables(sheet_name, contents)
        # all the parameters that have 2 variables
        elif (sheet_name in ['CapacityFactor']):
            result += 'param ' + sheet_name + ' default 1 := \n'
            result += _insert_two_variables(sheet_name, contents)
        # all the parameters that have 3 variables
        elif (sheet_name in ['EmissionActivityRatio', 'InputActivityRatio',
                             'OutputActivityRatio']):
            result += 'param ' + sheet_name + ' default 0 := \n'
            newRow = next(contents)
            newRow.pop(0)
            newRow.pop(0)
            newRow.pop(0)
            year = newRow.copy()
            for row in contents:
                result += '[SIMPLICITY, ' + \
                    row.pop(0) + ', ' + row.pop(0) + ', *, *]:'
                result += '\n'
                result += " ".join(year) + " "
                result += ':=\n'
                result += " ".join(row) + " "
                result += '\n'
            result += ';\n'
        # 8 #all the parameters that do not have variables
        elif (sheet_name in ['TotalTechnologyModelPeriodActivityUpperLimit']):
            result += 'param ' + sheet_name + ' default 9999999 : \n'
            result += _insert_no_variables(sheet_name, contents)
        elif (sheet_name in ['CapacityToActivityUnit']):
            result += 'param ' + sheet_name + ' default 1 : \n'
            result += _insert_no_variables(sheet_name, contents)
        # 8 #all the parameters that do not have variables
        elif (sheet_name in ['TotalTechnologyAnnualActivityLowerLimit']):
            result += 'param ' + sheet_name + ' default 0 := \n'
            result += _insert_no_variables(sheet_name, contents)
        # 8 #all the parameters that do not have variables
        elif (sheet_name in ['ModelPeriodEmissionLimit']):
            result += 'param ' + sheet_name + ' default 999999 := ;\n'
        # 8 #all the   parameters   that do not have variables
        elif (sheet_name in ['ModelPeriodExogenousEmission', 'AnnualExogenousEmission', 'OperationalLifeStorage']):
            result += 'param ' + sheet_name + ' default 0 := ;\n'
        elif (sheet_name in []):  # 8 #all the parameters that do not have variables
            result += 'param ' + sheet_name + ' default 0 := ;\n'
        # 8 #all the parameters that do not have variables
        elif (sheet_name in ['TotalTechnologyModelPeriodActivityLowerLimit']):
            result += 'param ' + sheet_name + ' default 0 := ;\n'
        # 8 #all the parameters that do not have variables
        elif (sheet_name in ['DepreciationMethod']):
            result += 'param ' + sheet_name + ' default 1 := ;\n'
        # 8 #all the parameters that do not have variables
        elif (sheet_name in ['OperationalLife']):
            result += 'param ' + sheet_name + ' default 1 : \n'
            result += _insert_no_variables(sheet_name, contents)
        elif (sheet_name in ['DiscountRate']):  # default value
            for row in contents:
                result += 'param ' + sheet_name + ' default 0.1 := ;\n'
        else:
            logger.debug("No code found for parameter %s", sheet_name)
    return result


def _insert_no_variables(name, contents):
    result = ""
    try:
        next(contents)
    except StopIteration:
        # The CSV file is empty
        pass
    firstColumn = []
    secondColumn = []
    secondColumn.append('SIMPLICITY')
    for row in contents:
        firstColumn.append(row[0])
        secondColumn.append(row[1])
    result += " ".join(firstColumn) + ' '
    result += ':=\n'
    result += " ".join(secondColumn) + ' '
    result += ';\n'
    return result


def _insert_two_variables(name, contents):
    result = ""
    newRow = next(contents)
    newRow.pop(0)
    newRow.pop(0)
    year = newRow.copy()
    for row in contents:
        result += '[SIMPLICITY, ' + row.pop(0) + ', *, *]:'
        result += '\n'
        result += " ".join(year) + " "
        result += ':=\n'
        result += " ".join(row) + " "
        result += '\n'
    result += ';\n'
    return result


def _insert_table(name, contents):
    result = ""
    try:
        newRow = contents[0]
        newRow.pop(0)  # removes the first element of the row
        result += " ".join((newRow)) + " "
    except StopIteration:
        # The CSV file is empty
        pass
    result += ':=\n'
    for row in contents[1:]:
        result += " ".join([str(x) for x in row]) + '\n'
    result += ';\n'
    return result


def _modify_names(sheet_names):
    """I change the name of the sheets in the xlsx file to match with the csv
    actual ones
    """
    modifiedNames = sheet_names.copy()
    for i in range(len(modifiedNames)):
        if (modifiedNames[i] == "TotalAnnualMaxCapacityInvestmen"):
            modifiedNames[i] = "TotalAnnualMaxCapacityInvestment"
        elif (modifiedNames[i] == "TotalAnnualMinCapacityInvestmen"):
            modifiedNames[i] = "TotalAnnualMinCapacityInvestment"
        elif (modifiedNames[i] == "TotalTechnologyAnnualActivityLo"):
            modifiedNames[i] = "TotalTechnologyAnnualActivityLowerLimit"
        elif (modifiedNames[i] == "TotalTechnologyAnnualActivityUp"):
            modifiedNames[i] = "TotalTechnologyAnnualActivityUpperLimit"
        elif (modifiedNames[i] == "TotalTechnologyModelPeriodActLo"):
            modifiedNames[i] = "TotalTechnologyModelPeriodActivityLowerLimit"
        elif (modifiedNames[i] == "TotalTechnologyModelPeriodActUp"):
            modifiedNames[i] = "TotalTechnologyModelPeriodActivityUpperLimit"
    return modifiedNames


if __name__ == '__main__':
    if len(sys.argv) != 3:
        msg = "Usage: python {} <workbook_filename> <output_filepath> <output_folder>"
        print(msg.format(sys.argv[0]))
        sys.exit(1)
    else:
        try:
            main(sys.argv[1], sys.argv[2], sys.argv[3])
        except:
            sys.exit(1)
