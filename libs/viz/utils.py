import matplotlib.pyplot as plt


# add value labels centered on bars 1% of max above the bar
def add_vbar_labels(x,y):
    """
    Short matplotlib util for adding value labels to vertical bar graph
    """
    for i in range(len(x)):
        plt.text(i, y[i]+(.01*max(y)), y[i], ha = 'center')
        

# add value labels centered on horiz bars 1% to the right
def add_hbar_labels(x,y):
    """
    Short matplotlib util for adding value labels to horizontal bar graph
    """
    for i, v in enumerate(y):
        plt.text(v + (.01*max(y)), i, str(v), ha = 'left', va= 'center')