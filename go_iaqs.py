import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import altair as alt
    return alt, mo, np, pd


@app.cell
def _(pd):
    iaqs_config = pd.read_csv("go_iaqs_table.csv")
    iaqs_config
    return (iaqs_config,)


@app.cell
def _(
    chart_output,
    max_concentration,
    min_concentration,
    mo,
    pollutant,
    rounding_strategy,
    step_concentration,
):
    mo.vstack(
        [
            mo.hstack([pollutant, min_concentration, max_concentration, step_concentration, rounding_strategy]),
            chart_output
        ]
    )
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
    # pollutant, concentration
    return (pollutant,)


@app.cell
def _(iaqs_config, mo, pd, pollutant):
    # UI for min/max concentration and step
    # Get default min/max concentrations based on the selected pollutant
    selected_pollutant_config = iaqs_config[iaqs_config["pollutant"] == pollutant.value]

    # Default min concentration: clow for 'Good' category
    default_min_concentration = selected_pollutant_config[
        selected_pollutant_config["category"] == "Good"
    ]["clow"].min()

    # Default max concentration: chigh for 'Unhealthy' category
    default_max_concentration = selected_pollutant_config[
        selected_pollutant_config["category"] == "Unhealthy"
    ]["chigh"].max()

    min_concentration = mo.ui.number(
        value=default_min_concentration if not pd.isna(default_min_concentration) else 0,
        start=0,
        step=0.1,
        label="Min Concentration"
    )

    max_concentration = mo.ui.number(
        value=default_max_concentration if not pd.isna(default_max_concentration) else 100,
        start=0,
        step=0.1,
        label="Max Concentration"
    )

    step_concentration = mo.ui.number(
        value=1.0,
        start=0.1,
        step=0.1,
        label="Concentration Step"
    )

    rounding_strategy = mo.ui.dropdown(
        options=["raw value", "round", "ceil", "floor"],
        value="raw value",
        label="Rounding Strategy"
    )

    # mo.hstack([min_concentration, max_concentration, step_concentration, rounding_strategy])
    return (
        max_concentration,
        min_concentration,
        rounding_strategy,
        step_concentration,
    )


@app.cell
def _(
    alt,
    calculate_aqi,
    iaqs_config,
    max_concentration,
    min_concentration,
    mo,
    np,
    pd,
    pollutant,
    rounding_strategy,
    step_concentration,
):
    # Simulate IAQS data
    concentrations = np.arange(
        min_concentration.value,
        max_concentration.value + step_concentration.value, # Include max_concentration
        step_concentration.value
    )

    simulated_data = []
    for conc in concentrations:
        raw_aqi = calculate_aqi(pollutant=pollutant.value, concentration=float(conc))

        if raw_aqi is not None:
            rounded_aqi = None
            if rounding_strategy.value == "round":
                rounded_aqi = np.round(raw_aqi)
            elif rounding_strategy.value == "ceil":
                rounded_aqi = np.ceil(raw_aqi)
            elif rounding_strategy.value == "floor":
                rounded_aqi = np.floor(raw_aqi)
            else: # "raw value"
                rounded_aqi = raw_aqi

            simulated_data.append({
                "concentration": conc,
                "raw_aqi": raw_aqi,
                "calculated_aqi": rounded_aqi
            })

    simulated_df = pd.DataFrame(simulated_data)

    # Initialize chart_output to None or a default message
    chart_output = None

    # Create the Altair plot
    if not simulated_df.empty:
        # Ensure units are available before trying to access iloc[0]
        pollutant_units = iaqs_config[iaqs_config['pollutant'] == pollutant.value]['units']
        unit_label = pollutant_units.iloc[0] if not pollutant_units.empty else "units"

        chart_output = alt.Chart(simulated_df).mark_line(point=True).encode(
            x=alt.X("concentration:Q", title=f"Concentration ({unit_label})"),
            y=alt.Y("calculated_aqi:Q", title=f"Calculated AQI ({rounding_strategy.value})"),
            tooltip=[
                alt.Tooltip("concentration:Q", title="Concentration"),
                alt.Tooltip("raw_aqi:Q", title="Raw AQI")
            ]
        ).properties(
            title=f"Simulated AQI for {pollutant.value} ({rounding_strategy.value} values)"
        ).interactive()
    else:
        chart_output = mo.md(f"No data to display for **{pollutant.value}** with the selected concentration range. Please adjust the pollutant, min/max concentration, or step.")

    # chart_output
    return (chart_output,)


if __name__ == "__main__":
    app.run()
