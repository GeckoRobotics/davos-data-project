import pandas as pd
import requests

from ..inspection_analysis.tokens import token


# production url components for portal-service deliverables
prod = {
    "url_start": "https://portal-service.cloud.geckorobotics.com/api/v1/deliverables/",
    "url_end": "/binned_plot_data.json", 
    "token": token
}

# headers
headers = {
    "accept": "application/json", 
    "Authorization": f"Bearer {prod['token']}"
}


# simplest request inspection df from portal service
def get_inspection_df(inspection_slug):
    """
    Take an inspection slug and return the inspection_df
    
    inputs:
        - inspection slug as string
    outputs:
        - inspection_df with columns:
            - plot_y
            - customer_x
            - x_bin
            - customer_y
            - y_bin
            - plot_x
            - thickness
    """
    
    print(f"Making Req...")
    req = requests.get(f"{prod['url_start']}{inspection_slug}{prod['url_end']}", headers=headers)
    #print(f"\tRequest Text: {req.text}")
    print(f"...Req Done")
    
    try:
        inspection_df = pd.DataFrame(req.json()['plots'][0]['data'])
    except:
        print(f"\tRequest Text: {req.text}")
    
    return inspection_df


# main utility for analyzing a single inspection df
def analyze_inspection_df(inspection_df, nominal, threshold):
    """
    Take inspection df and return key thickness stats based on target threshold
    
    inputs:
        - inspection_df - binned data from inspection
        - nominal - designed thickness, t at time 0
        - threshold - target threshold for count (ie 40% => threshold = .6)
    output:
        - min_t - the min thickness bin
        - max_t - the max thickness bin
        - tubes_inspected - count of the number of unique customer_x
        - bins_collected - count of bins
        - critical_tubes_count - count of customer_x where >= 1 t is < target t
        - critical_bins_count - count of bins where t is < target t
    """
    # get min/max
    min_t = inspection_df.thickness.min()
    max_t = inspection_df.thickness.max()
    
    # calculate target t from nominal and threshold (example: .6*nominal = target)
    target = nominal*threshold
    
    # count tubes (or stripes ?) and bins
    tubes_inspected = inspection_df.customer_x.nunique()
    bins_collected = inspection_df.shape[0]
    
    # get min t per bin
    min_t_by_tube_list = inspection_df.groupby(['customer_x'])['thickness'].min().to_list()
    
    # count tubes and bins with critical reading
    critical_tubes_count = len([t for t in min_t_by_tube_list if t < target])
    critical_bins_count = len([t for t in inspection_df.thickness if t < target])
    
    return min_t, max_t, tubes_inspected, bins_collected, critical_tubes_count, critical_bins_count


# get histogram analysis of inspection_df
def hist_inspection_df(inspection_df, nominal):
    """
    Take inspection df and return key stats for a range of thickness thresholds
    inputs:
        - inspection_df - binned data from inspection
        - nominal - designed thickness, t at time 0
    outputs:
        - min_t - the min thickness bin
        - max_t - the max thickness bin
        - tubes_inspected - count of the number of unique customer_x
        - bins_collected - count of bins
        - tube_hist_bin_counts - list of # of crit tubes based on each threshold bin
        - bin_hist_bin_counts - list of # of crit bins based on each threshold bin
    """
    # get min/max
    min_t = inspection_df.thickness.min()
    max_t = inspection_df.thickness.max()
    
    # list of target bins (defined as a % loss, so .1 = 10% loss from nominal)
    bins = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    
    # count tubes (or stripes ?) and bins 
    tubes_inspected = inspection_df.customer_x.nunique()
    bins_collected = inspection_df.shape[0]
    
    # get min t per bin
    min_t_by_tube_list = inspection_df.groupby(['customer_x'])['thickness'].min().to_list()
    
    # initialize empty lists
    tube_hist_bin_counts = []
    bin_hist_bin_counts = []
    
    # iterate through target bins, count tubes and bins w t < target
    for bini in bins:
        # TODO: unused atm, but would be better way to create column headers
        bin_string = '{}%'.format(str(round(bini*100))) + ' Loss'
        # define target
        target = nominal*(1-bini)
        # calculate crit counts
        critical_tubes_count = len([t for t in min_t_by_tube_list if t < target])
        critical_bins_count = len([t for t in inspection_df.thickness if t < target])
        # append to lists
        tube_hist_bin_counts.append(critical_tubes_count)
        bin_hist_bin_counts.append(critical_bins_count)
        
    
    return min_t, max_t, tubes_inspected, bins_collected, tube_hist_bin_counts, bin_hist_bin_counts


# check_thickness does large scale analysis of a df containing inspection slugs
def check_thickness(targets_df, threshold):
    """
    Takes a dataframe of target inspection slugs and their nominals and returns analysis data
    inputs: 
        - targets_df - contains slug and nominal headers
        - threshold - float (example = 0.6)
    outputs: 
        - data_df - df containing the following columns where 1 row is one inspection
            - columns:
                - 'slug'
                - 'nominal'
                - 'min_t'
                - 'max_t'
                - 'tubes_inspected'
                - 'bins_collected'
                - 'critical_tubes'
                - 'critical_bins'
        - error_list - list of slugs where an error was encountered
    """
    # initialize empy lists
    data_list = []
    error_slug_list = []

    # iterate through target inspections
    for row in range(len(targets_df)):
        inspection_slug = targets_df.loc[row, 'slug']
        nominal = targets_df.loc[row, 'nominal']
        
        # print every tenth row num as a progress tracker
        if row%10 == 0:
            print('{}/{}'.format(row, targets_df.shape[0]))
            
        ## clean data for hallador units with bad nominals
        hallador_unit_1 = ['20220523-332ac6', '20220523-64417d']
        hallador_unit_2 = ['20221011-7c7e5f', '20221011-18c8e9']
        
        if inspection_slug in hallador_unit_1:
            nominal = 0.28
        if inspection_slug in hallador_unit_2:
            nominal = 0.26
        # end hackery for bad nominals

        # req for inspection data
        req = requests.get(f"{prod['url_start']}{inspection_slug}{prod['url_end']}", headers=headers)
        # if we got data...
        if req.json():
            try:
                # convert to df
                inspection_df = pd.DataFrame(req.json()['plots'][0]['data'])

                # analyze the df returned
                min_t, max_t, tubes_inspected, bins_collected, critical_tubes_count, critical_bins_count = analyze_inspection_df(inspection_df, nominal, threshold)

                # convert to a row
                data = [inspection_slug, nominal, min_t, max_t, tubes_inspected, bins_collected, critical_tubes_count, critical_bins_count]
                
                # append row to list
                data_list.append(data)
            except:
                print('Error: No plots record on req.json ...')
                error_slug_list.append(inspection_slug)
            
        else:
            print('Inspection slug failed to return data: {}'.format(inspection_slug))

    # compile data list of lists into dataframe
    data_df = pd.DataFrame(data_list, columns=['slug', 'nominal', 'min_t', 'max_t', 'tubes_inspected', 'bins_collected', 'critical_tubes', 'critical_bins'])
    
    return data_df, error_slug_list


# get histogram analysis for targets df
def get_thickness_histogram(targets_df):
    """
    Takes a dataframe of target inspection slugs and nominals and returns histogram analysis data
    inputs: 
        - targets_df - contains slug and nominal headers
    outputs:
        - data_df - df containing the following columns where 1 row is one inspection
            - columns:
                - 'slug'
                - 'nominal'
                - 'min_t'
                - 'max_t'
                - 'tubes_inspected'
                - 'bins_collected'
                - Tubes by Loss bin
                - Bins by Loss bin
        - error_list - list of slugs where an error was encountered
    """
    # initialize empty lists
    data_list = []
    error_slug_list = []

    # iterate through target inspections
    for row in range(len(targets_df)):
        inspection_slug = targets_df.loc[row, 'slug']
        nominal = targets_df.loc[row, 'nominal']
        
        # print every tenth row num as a progress tracker
        if row%10 == 0:
            print('{}/{}'.format(row, targets_df.shape[0]))
            
        ## clean data for hallador units with bad nominals
        hallador_unit_1 = ['20220523-332ac6', '20220523-64417d']
        hallador_unit_2 = ['20221011-7c7e5f', '20221011-18c8e9']
        
        if inspection_slug in hallador_unit_1:
            nominal = 0.28
        if inspection_slug in hallador_unit_2:
            nominal = 0.26
        # hack gibson slopes nominal
        if inspection_slug == '20221004-565f7b':
            nominal = 0.203
        # end hackery for bad nominals

        # req for inspection data
        req = requests.get(f"{prod['url_start']}{inspection_slug}{prod['url_end']}", headers=headers)
        # if we got data...
        if req.json():
            try:
                # convert to df
                inspection_df = pd.DataFrame(req.json()['plots'][0]['data'])

                # analyze the df returned
                min_t, max_t, tubes_inspected, bins_collected, tube_hist_bin_counts, bin_hist_bin_counts = hist_inspection_df(inspection_df, nominal)
                
                # add 40%loss per 10k bins stat:
                crits_per10k = round(((bin_hist_bin_counts[3])/bins_collected)*10000)

                # convert to a row
                data = [inspection_slug, nominal, min_t, max_t, tubes_inspected, bins_collected, crits_per10k] + tube_hist_bin_counts + bin_hist_bin_counts

                # append row to list
                data_list.append(data)
            except:
                print('Error: No plots record on req.json ...')
                error_slug_list.append(inspection_slug)
            
        else:
            print('Inspection slug failed to return data: {}'.format(inspection_slug))

    # build data df
    data_df = pd.DataFrame(data_list, columns=[
        'slug', 
        'nominal', 
        'min_t', 
        'max_t', 
        'tubes_inspected', 
        'bins_collected',
        'crits_per10k',
        'Tubes w 10% Loss',
        'Tubes w 20% Loss',
        'Tubes w 30% Loss',
        'Tubes w 40% Loss',
        'Tubes w 50% Loss',
        'Tubes w 60% Loss',
        'Tubes w 70% Loss',
        'Tubes w 80% Loss',
        'Tubes w 90% Loss',
        'Bins w 10% Loss',
        'Bins w 20% Loss',
        'Bins w 30% Loss',
        'Bins w 40% Loss',
        'Bins w 50% Loss',
        'Bins w 60% Loss',
        'Bins w 70% Loss',
        'Bins w 80% Loss',
        'Bins w 90% Loss',
    ])
    
    return data_df, error_slug_list


# standardized function for grouping the comb_df
def group_critdat(comb_df, groupon_list):
    """
    Takes the comb_df and a groupon_list and returns a sorted, grouped df
    
    Inputs:
        - comb_df - return of check_thickness merged with reference data
        - groupon_list - list of ref_df columns to groupby
    Outputs:
        - grouped df w sum of analysis metrics
    """
    # groupby crit analysis and sum
    crits_df = comb_df.groupby(groupon_list)[
        'tubes_inspected',	
        'bins_collected', 
        'critical_tubes', 
        'critical_bins'
    ].sum().reset_index()
    # groupby and count inspections
    count_df = comb_df.groupby(groupon_list)['slug'].nunique().to_frame().reset_index()
    # merge the counts and the summed crit analysis
    merged_df = count_df.merge(crits_df, how='outer', on=groupon_list)
    # rename slug to inspections (count of)
    merged_df.rename(columns={'slug': 'inspections'}, inplace=True)
    
    return merged_df


#
