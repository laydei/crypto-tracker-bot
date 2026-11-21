import mplfinance as mpf

# Configuration

custom_colors = mpf.make_marketcolors(
    up='#26a69a',
    down='#ef5350',
    edge='inherit',
    wick='inherit',
    volume='inherit', 
)

custom_style = mpf.make_mpf_style(
    base_mpf_style='charles',
    marketcolors=custom_colors,
    facecolor='#151924',
    figcolor='#151924',
    gridcolor='#475569',
    gridstyle='--',
    rc={
        'font.weight': 'normal',
        'axes.labelweight': 'normal',
        'axes.titleweight': 'bold',
        'figure.titleweight': 'bold',
        
        'text.color': '#94a3b8',
        'axes.labelcolor': '#94a3b8',   
        'xtick.color': '#94a3b8',
        'ytick.color': '#94a3b8',
        'grid.linewidth': 0.8,

        'axes.spines.top': False,
        'axes.spines.bottom': False,
        'axes.spines.left': False,
        'axes.spines.right': False,
        'axes.linewidth': 0,
        'axes.edgecolor': '#151924',
    }
)