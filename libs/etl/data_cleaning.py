import pandas as pd


# AEP Tube Failure Data
def generate_aep_outage_dfs():
    """
    This function will read the raw AEP Tube leak data and produce
    cleaned datasets for active only and all tube leaks
    """
    # get raw data
    aep_df = pd.read_excel(r"../data/raw_data/AEP Plants 2011-20220802 Boiler Tube Leaks.xlsx", "Data")
    
    # enrich
    aep_df['Outage Month'] = pd.to_datetime(aep_df['Event Start Timestamp']).dt.month
    aep_df['Outage Week'] = pd.to_datetime(aep_df['Event Start Timestamp']).dt.isocalendar().week
    
    # non-retired only
    active_aep_df = aep_df[aep_df['Retired Flag']=='N']
    
    return aep_df, active_aep_df


# Duke Tube Failure Data
def generate_duke_outage_dfs():
    """
    This function will read the raw Duke Tube leak data and produce
    cleaned datasets for active only and all tube leaks
    """
    # get raw data
    duke_df = pd.read_csv(r"../data/raw_data/Duke Fleet Boiler tube failure data 2005 - 2020.csv")
    
    # enrich
    duke_df['Outage Month'] = pd.to_datetime(duke_df['Start Date']).dt.month
    duke_df['Outage Week'] = pd.to_datetime(duke_df['Start Date']).dt.isocalendar().week
    
    return duke_df


# IIR US Boiler data
def generate_iir_boilers_dfs():
    """
    This function will read the raw iir US boilers data and produce
    cleaned datasets for operational only and all
    """
    # get raw data
    us_boilers_df = pd.read_csv(r"../data/raw_data/All US Boilers.csv")
    
    # enrich with shutdown date and year
    us_boilers_df['SHUTDOWN_dt'] = pd.to_datetime(us_boilers_df['SHUTDOWN'])
    us_boilers_df['SHUTDOWN_yr'] = us_boilers_df['SHUTDOWN_dt'].dt.year
    
    # filter for operational only
    operational_us_boilers_df = us_boilers_df[us_boilers_df['U_STATUS']=='Operational']
    
    return us_boilers_df, operational_us_boilers_df