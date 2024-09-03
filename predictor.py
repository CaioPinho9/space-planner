import json

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt


class Predictor:
    _predict_parameters_file_name = 'fitted_parameters.csv'  # File to save the parameters
    _predict_parameters = None

    # Define the exponential function
    @staticmethod
    def __exponential_func(x, a, b):
        return a * b ** x

    @staticmethod
    def write_csv(file_name, data):
        # Create a DataFrame from the dictionary and write to CSV
        df = pd.DataFrame(data)
        df.to_csv(file_name, index=False)

    @staticmethod
    def __plot_function(df, output_data, x_values):
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

    # Fit the exponential model and return the fitted values
    @classmethod
    def __fit_exponential_curve(cls, x_values, y_values):
        params, _ = curve_fit(Predictor.__exponential_func, x_values, y_values)
        a, b = params
        y_fitted = cls.__exponential_func(np.array(x_values), a, b)
        return y_fitted, a, b

    # Main function
    @classmethod
    def generate_parameters(cls, plot=False):
        # Read JSON data from a file
        json_file_path = 'thing_price_evolution.json'
        with open(json_file_path, 'r') as file:
            json_data = json.load(file)

        # Convert lists to pandas Series to handle different lengths
        df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in json_data.items()]))

        # Determine x_values
        if 'x' in df.columns:
            x_values = df['x'].values
        else:
            x_values = np.arange(1, len(df) + 1)

        # Prepare data for saving
        output_data = {'x': x_values}
        predict_parameters = {'Column': [], 'a': [], 'b': []}

        # Process each column
        for column in df.columns:
            # And has more than 1 non nan value
            if column != 'x':
                y_values = df[column].values

                mask = ~np.isnan(y_values)
                y_values = y_values[mask]
                x_values_filtered = x_values[mask]

                if len(y_values) == 0:
                    continue  # Skip columns with no valid values

                # Fit the curve
                if sum(~np.isnan(df[column])) > 1:
                    y_fitted, a, b = cls.__fit_exponential_curve(x_values_filtered, y_values)
                else:
                    a = y_values[0] * 0.85
                    y_fitted = y_values

                # Add fitted values to the output data
                output_data[f'{column} Original y'] = y_values
                output_data[f'{column} Fitted y'] = y_fitted

                # Store predict_parameters for each column
                predict_parameters['Column'].append(column)
                predict_parameters['a'].append(a)
                predict_parameters['b'].append(b)

                # Print model details
                print(f'{column}: y = {a:.2f} * {b:.2f}^x')

        # Write the predict_parameters to a CSV file
        Predictor.write_csv(cls._predict_parameters_file_name, predict_parameters)
        cls._predict_parameters = predict_parameters

        # Plot the results
        if plot:
            Predictor.__plot_function(df, output_data, x_values)

    @classmethod
    def get_predict_parameters(cls):
        if cls._predict_parameters is None:
            cls._predict_parameters = pd.read_csv(cls._predict_parameters_file_name)
        return cls._predict_parameters

    # Method to read parameters and make predictions
    @classmethod
    def predict_thing_cost(cls, value, thing):
        # Read the parameters from the CSV file
        df = cls.get_predict_parameters()

        # Iterate over each row in the dataframe
        for _, row in df.iterrows():
            if row['Column'] != thing:
                continue

            a = row['a']
            b = row['b']

            # Predict y values using the exponential function
            return round(cls.__exponential_func(value, a, b))

        return None


if __name__ == '__main__':
    Predictor.generate_parameters(plot=True)
