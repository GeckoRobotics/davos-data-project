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


# create new feature component type derived from string
def determine_component(string):
    """
    Take a component slug and derive the component type
    """
    component_type = 'Other'
    
    if 'slope' in str(string).lower():
        component_type = 'Slope'
    if 'wall' in str(string).lower():
        component_type = 'Wall'
    if 'division' in str(string).lower():
        component_type = 'Division Wall'
    if 'arch' in str(string).lower():
        component_type = 'Arch'
    if 'bull' in str(string).lower():
        component_type = 'Bullnose'
    if 'economizer' in str(string).lower():
        component_type = 'Backpass'
    if 'evaporator' in str(string).lower():
        component_type = 'Backpass'
    if 'superheater' in str(string).lower():
        component_type = 'Backpass'
        
    if component_type == 'Other':
        str_list = string.lower().split('-')[:-1]
        component_type = '-'.join(str_list)
    
    return component_type


# derive all_us_boilers - boil_info tags

# derive the burner config
def derive_boiler_config(boil_info):
    """
    Derive the boiler configuration field from the boil_info
    """
    # Burner configurations:
    tang_config_tags = ['Tangential-Fired', 'Tangential', 'Tangential-Firing', 'Tangentially-Fired', 'Tangential/Concentric-Fired']
    front_config_tags = ['Front-Fired']
    opp_config_tags = ['Opposed-Fired']
    arch_config_tags = ['Arch-Fired']
    stoker_config_tags = ['Stoker-Fired']
    cyclone_config_tags = ['Cyclone-Fired', 'Cyclone']
    
    # initialize the boiler configuration
    boil_config = 'Unknown'
    
    # loop for each configuration
    for tag in tang_config_tags:
        if tag in boil_info:
            boil_config = 'Tangential'
            
    for tag in front_config_tags:
        if tag in boil_info:
            boil_config = 'Front'
            
    for tag in opp_config_tags:
        if tag in boil_info:
            boil_config = 'Opposed'
            
    for tag in arch_config_tags:
        if tag in boil_info:
            boil_config = 'Arch'
            
    for tag in stoker_config_tags:
        if tag in boil_info:
            boil_config = 'Stoker'
            
    for tag in cyclone_config_tags:
        if tag in boil_info:
            boil_config = 'Cyclone'
    
    return boil_config


# derive the boiler type
def derive_boiler_type(boil_info):
    """
    Derive the boiler type from the boil_info
    """
    # boiler type tags
    pc_type_tags = ['PC']
    cfb_type_tags = ['CFB', 'Circulating Fluidized Bed']
    
    # initialize the boiler type
    boil_type = 'Unknown'
    
    # loop for each type
    for tag in pc_type_tags:
        if tag in boil_info:
            boil_type = 'PC'
            
    for tag in cfb_type_tags:
        if tag in boil_info:
            boil_type = 'CFB'
            
    return boil_type


# derive criticality
def derive_criticality(boil_info):
    """
    Assign criticality based on tags
    """
    criticality = "none"
    
    if "critical" in boil_info.lower():
        criticality = "Critical"
    if "subcritical" in boil_info.lower():
        criticality = "Subcritical"
    if "supercritical" in boil_info.lower():
        criticality = "Supercritical"
    if "ultrasupercritical" in boil_info.lower():
        criticality = "Ultrasupercritical"
        
    return criticality
    


# IIR US Boiler data
def generate_iir_boilers_dfs():
    """
    This function will read the raw iir US boilers data and produce
    cleaned datasets for operational only and all
    """
    # get raw data
    us_boilers_df = pd.read_csv(r"../data/raw_data/All US Boilers.csv")
    
    # enrich dataset w derived values
    # shutdown date and year
    us_boilers_df['SHUTDOWN_dt'] = pd.to_datetime(us_boilers_df['SHUTDOWN'])
    us_boilers_df['SHUTDOWN_yr'] = us_boilers_df['SHUTDOWN_dt'].dt.year
    # boiler type and burner configuration
    us_boilers_df['BOIL_INFO'] = us_boilers_df['BOIL_INFO'].astype(str)
    us_boilers_df['BOIL_CONFIG'] = us_boilers_df['BOIL_INFO'].apply(lambda x: derive_boiler_config(x))
    us_boilers_df['BOIL_TYPE_Tag'] = us_boilers_df['BOIL_INFO'].apply(lambda x: derive_boiler_type(x))
    
    # assign critical indicator
    us_boilers_df['Criticality'] = us_boilers_df['BOIL_INFO'].apply(lambda x: derive_criticality(x))
    
    # filter for operational only
    operational_us_boilers_df = us_boilers_df[us_boilers_df['U_STATUS']=='Operational']
    
    return us_boilers_df, operational_us_boilers_df