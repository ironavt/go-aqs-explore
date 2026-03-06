import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import altair as alt
    return mo, np, pd


@app.cell
def _(pd):
    iaqs_config = pd.read_csv("go_iaqs_table.csv")
    iaqs_config
    return (iaqs_config,)


@app.cell
def _():
    return


@app.cell
def _(iaqs_config):
    def calculate_aqi(pollutant: str, concentration: float) -> float | None:
        """
        Calculates the Air Quality Index (AQI) for a given pollutant and concentration
        using the provided formula and iaqs_config data.

        Args:
            pollutant (str): The name of the pollutant (e.g., "PM2.5").
            concentration (float): The concentration value for the pollutant.

        Returns:
            float | None: The calculated AQI, or None if the pollutant or concentration
                          range is not found in the configuration.
        """
        # Filter for the specific pollutant
        pollutant_config = iaqs_config[iaqs_config["pollutant"] == pollutant]

        if pollutant_config.empty:
            return None

        # Find the category where the concentration falls
        matching_row = pollutant_config[
            (pollutant_config["clow"] <= concentration) &
            (pollutant_config["chigh"] >= concentration)
        ]

        if matching_row.empty:
            # If no matching row is found, check if the concentration is higher than the highest chigh
            max_chigh = pollutant_config["chigh"].max()
            if concentration > max_chigh:
                return 0.0  # Return 0 if concentration is higher than the highest defined range
            else:
                return None # Otherwise, concentration is below the lowest clow or in a gap, return None

        # If multiple rows match (should not happen with well-defined ranges), take the first one
        row = matching_row.iloc[0]

        ihigh = row["ihigh"]
        ilow = row["ilow"]
        chigh = row["chigh"]
        clow = row["clow"]

        # Handle division by zero if chigh == clow, though unlikely for concentration ranges
        if chigh == clow:
            # If the range is a single point and concentration matches, the index is ilow
            # Otherwise, it's an invalid range for interpolation.
            if concentration == clow:
                index_part = ilow
            else:
                return None # Concentration outside a single-point range
        else:
            # Calculate the interpolated index part
            index_part = ((ihigh - ilow) / (chigh - clow)) * (concentration - clow) + ilow

        # Apply the user's specific formula
        aqi = 10 - index_part
        return aqi
    return (calculate_aqi,)


@app.cell
def _(iaqs_config, mo):
    pollutant = mo.ui.dropdown(
        options=iaqs_config['pollutant'].unique(),
        value="PM2.5",
        label="Choose pollutant"
    )
    concentration = mo.ui.number(value=0,start=0,step=1)
    pollutant, concentration
    return concentration, pollutant


@app.cell
def _(calculate_aqi, concentration, mo, np, pollutant):
    raw_index = calculate_aqi(pollutant=pollutant.value, concentration=float(concentration.value))
    round_index = np.round(raw_index)
    ceil_index = np.ceil(raw_index)
    floor_index = np.floor(raw_index)

    text = f"""
    Raw index: {raw_index}

    Round index: {round_index}

    Ceil index: {ceil_index}
    """
    mo.md(text)
    return


if __name__ == "__main__":
    app.run()
