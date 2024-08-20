from math import isnan

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# Define the exponential function
def exponential_func(x, a, b):
    return a * b ** x

# Read data from CSV file
def read_csv(file_name):
    df = pd.read_csv(file_name)
    return df

# Fit the exponential model and return the fitted values
def fit_exponential_curve(x_values, y_values):
    params, _ = curve_fit(exponential_func, x_values, y_values)
    a, b = params
    y_fitted = exponential_func(np.array(x_values), a, b)
    return y_fitted, a, b

# Write data to a new CSV file
def write_csv(file_name, data):
    # Create a DataFrame from the dictionary and write to CSV
    df = pd.DataFrame(data)
    df.to_csv(file_name, index=False)

output_csv = 'fitted_parameters.csv'  # File to save the parameters

# Main function
def generate_exponentials():
    input_csv = 'real_values.csv'  # Replace with your input CSV file

    # Read data
    df = read_csv(input_csv)

    # Determine x_values
    if 'x' in df.columns:
        x_values = df['x'].values
    else:
        x_values = np.arange(1, len(df) + 1)

    # Prepare data for saving
    output_data = {'x': x_values}
    parameters = {'Column': [], 'a': [], 'b': []}

    # Process each column
    for column in df.columns:
        if column != 'x':  # Skip 'x' column if present
            y_values = df[column].values

            mask = ~np.isnan(y_values)
            y_values = y_values[mask]
            x_values_filtered = x_values[mask]

            if len(y_values) == 0:
                continue  # Skip columns with no valid values

            # Fit the curve
            y_fitted, a, b = fit_exponential_curve(x_values_filtered, y_values)

            # Add fitted values to the output data
            output_data[f'{column} Original y'] = y_values
            output_data[f'{column} Fitted y'] = y_fitted

            # Store parameters for each column
            parameters['Column'].append(column)
            parameters['a'].append(a)
            parameters['b'].append(b)

            # Print model details
            print(f'{column}: y = {a:.2f} * {b:.2f}^x')

    # Write the parameters to a CSV file
    write_csv(output_csv, parameters)

    # Plot the results
    for column in df.columns:
        if column != 'x' and column + ' Original y' in output_data.keys():
            y_values = df[column].values
            mask = ~np.isnan(y_values)
            y_values = y_values[mask]
            x_values_filtered = x_values[mask]

            # Check if x and y have the same length
            if len(x_values_filtered) != len(y_values):
                print(f"Warning: x and y have different lengths for column {column}: x_length={len(x_values_filtered)}, y_length={len(y_values)}")
                continue  # Skip this column if lengths mismatch

            plt.figure(figsize=(14, 8))
            plt.scatter(x_values_filtered, y_values, label=f'Original {column}')
            plt.plot(x_values_filtered, output_data[f'{column} Fitted y'][:len(x_values_filtered)], label=f'Fitted {column}')
            plt.xlabel('x')
            plt.ylabel('y')
            plt.title('Exponential Fit to Data')
            plt.legend()
            plt.grid(True)
            plt.show()


# Method to read parameters and make predictions
def predict_from_csv(x, column):
    # Read the parameters from the CSV file
    df = pd.read_csv(output_csv)

    # Iterate over each row in the dataframe
    for _, row in df.iterrows():
        if row['Column'] != column:
            continue

        a = row['a']
        b = row['b']

        # Predict y values using the exponential function
        return round(exponential_func(x, a, b))

    return None
if __name__ == '__main__':
    generate_exponentials()
    print(predict_from_csv(18, "SolarPanel"))
