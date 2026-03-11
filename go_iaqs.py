import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium", app_title="GO IAQS Sim")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import altair as alt
    import io
    return alt, io, mo, np, pd


@app.cell
def _():
    iaqs_config_csv = """pollutant,units,category,clow,chigh,ilow,ihigh
    PM2.5,μg/m3,Good,0,10,0,2
    PM2.5,μg/m3,Moderate,11,25,3,6
    PM2.5,μg/m3,Unhealthy,26,100,7,10
    CO2,ppm,Good,450,800,0,2
    CO2,ppm,Moderate,801,1400,3,6
    CO2,ppm,Unhealthy,1401,5000,7,10
    CO,ppm,Good,0,1.7,0,2
    CO,ppm,Moderate,1.8,9.0,3,6
    CO,ppm,Unhealthy,9.1,31,7,10
    CH2O,ppb,Good,0,27,0,2
    CH2O,ppb,Moderate,28,100,3,6
    CH2O,ppb,Unhealthy,101,500,7,10
    O3,ppb,Good,0,25,0,2
    O3,ppb,Moderate,26,100,3,6
    O3,ppb,Unhealthy,101,300,7,10
    NO2,ppb,Good,0,21,0,2
    NO2,ppb,Moderate,22,100,3,6
    NO2,ppb,Unhealthy,101,250,7,10
    Radon,Bq/m3,Good,0,100,0,2
    Radon,Bq/m3,Moderate,101,150,3,6
    Radon,Bq/m3,Unhealthy,151,300,7,10
    """
    categories_config_csv = """category,ilow,ihigh
    Good,0,2
    Moderate,3,6
    Unhealthy,7,10"""
    return categories_config_csv, iaqs_config_csv


@app.cell
def _(mo, tab1, tab2):
    tabs = mo.ui.tabs(
        {
            "Playground": tab1,
            "Configuration": tab2
        }
    )
    return (tabs,)


@app.cell
def _(mo, table_iaqs_config, tabs):
    mo.vstack([tabs, table_iaqs_config])
    return


@app.cell
def _(calculate_aqi):
    calculate_aqi("PM2.5", 10.2)
    return


@app.cell
def _(categories_config_csv, iaqs_config_csv, mo):
    # Text areas with configs
    text_aqi_config = mo.ui.text_area(
        value=iaqs_config_csv,
        full_width=True,
        label="Enter pollutants config CSV:"
    )
    text_categories_config = mo.ui.text_area(
        value=categories_config_csv,
        full_width=True,
        label="Enter categories config:"
    )
    return text_aqi_config, text_categories_config


@app.cell
def _(io, pd, text_aqi_config, text_categories_config):
    # Orig dataframes
    iaqs_config_raw = pd.read_csv(io.StringIO(text_aqi_config.value))
    categories_df = pd.read_csv(io.StringIO(text_categories_config.value), index_col="category")
    return categories_df, iaqs_config_raw


@app.cell
def _(iaqs_config_raw, mo):
    # Copy config df editor
    iaqs_config_editor = mo.ui.dataframe(iaqs_config_raw)
    return (iaqs_config_editor,)


@app.cell
def _(categories_df, iaqs_config_editor):
    # Create a new DataFrame based on the editor's value and apply slider adjustments.
    # This ensures iaqs_config is re-assigned when sliders or the editor change.
    # We start with a fresh copy of the base configuration from the editor's value
    # to ensure all changes are applied to a new object.
    _updated_iaqs_config = iaqs_config_editor.value.copy()

    # Apply the ilow and ihigh values from categories_df to this new DataFrame
    _updated_iaqs_config["ilow"] = _updated_iaqs_config["category"].map(categories_df["ilow"])
    _updated_iaqs_config["ihigh"] = _updated_iaqs_config["category"].map(categories_df["ihigh"])

    # Re-assign iaqs_config to this newly adjusted DataFrame.
    # This re-assignment is crucial for Marimo's reactivity to detect the change
    # and trigger all downstream cells (like calculate_aqi, simulated_df, and chart_output).
    iaqs_config = _updated_iaqs_config
    return (iaqs_config,)


@app.cell
def _(iaqs_config, mo):
    # UI element, displays current IAQ config
    table_iaqs_config = mo.ui.table(
        iaqs_config,
        pagination=False,
        label="Current IAQS config"
    )
    return (table_iaqs_config,)


@app.cell
def _(
    chart_output,
    max_concentration,
    min_concentration,
    mo,
    pollutant,
    rounding_strategy,
    step_concentration,
    text_aqi_config,
    text_categories_config,
):
    tab1 = mo.vstack(
        [
            mo.hstack([pollutant, min_concentration, max_concentration, step_concentration, rounding_strategy]),
            chart_output
        ]
    )
    tab2 = mo.vstack(
        [
            mo.hstack([text_aqi_config, text_categories_config], widths=[2, 1]),
            mo.md(text="**Categories config** redefines `ilow` and `ihigh` in the **pollutants config.** Press **Ctrl + Enter** (^ + Return) or click outside the text area to update values.")
        ]
    )
    return tab1, tab2


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
    # UI element: dropdown to choose pollutant
    pollutant = mo.ui.dropdown(
        options=iaqs_config['pollutant'].unique(),
        value=iaqs_config['pollutant'].unique()[0],
        label="Choose pollutant"
    )
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
        step=1,
        label="Min Concentration"
    )

    max_concentration = mo.ui.number(
        value=default_max_concentration if not pd.isna(default_max_concentration) else 100,
        start=0,
        step=1,
        label="Max Concentration"
    )

    step_concentration = mo.ui.number(
        value=1.0,
        start=0.1,
        step=0.1,
        label="Concentration Step"
    )

    rounding_strategy = mo.ui.dropdown(
        options=["raw", "round", "ceil", "floor"],
        value="raw",
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
    # so marimo correctly tracks this object
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
        )#.interactive()
    else:
        chart_output = mo.md(f"No data to display for **{pollutant.value}** with the selected concentration range. Please adjust the pollutant, min/max concentration, or step.")
    return (chart_output,)


if __name__ == "__main__":
    app.run()
