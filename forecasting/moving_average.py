def moving_average(data, window_size):
    """
    Returns the moving average of a list of values over a specified window size.
    """
    if not data or window_size <= 0:
        return []

    averages = []
    for i in range(len(data) - window_size + 1):
        avg = sum(data[i:i + window_size]) / window_size
        averages.append(avg)
    
    return averages

