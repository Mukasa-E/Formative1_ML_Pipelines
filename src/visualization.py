import matplotlib.pyplot as plt

def plot_close_price(df):
    plt.figure()
    plt.plot(df['date'], df['Close'])
    plt.xlabel("Date")
    plt.ylabel("Close Price")
    plt.title("Stock Closing Price Over Time")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()