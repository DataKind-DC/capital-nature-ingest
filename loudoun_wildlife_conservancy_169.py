"""Scrapes Loudoun Wildlife Conservancy calendar through
February 2020, creates pandas dataframe of calendar information."""

import pandas as pd


def event_calendar(uri, name, start, stop):
    """
    Creates event calendar from Loudon Wildlife Conservatory
    website.

    Scrapes data for the month in question, and converts it into
    a dataframe with the month and day listed, as well as any
    events for the day.

    Parameters:
    uri: The uri for the calendar month in question.
    name: The name of the month.
    start: The number of days at the beginning of the calendar
           that are from the previous month. For example, if the
           month starts on a Sunday, the calendar shows six
           days (Mon-Sat) from the prior month listed before this.
    stop: The number of days at the end of the calendar that are
          from the upcoming month.

    Returns:
    month_data = dataframe for month in question
    """

    # Download December calendar data
    month = (pd.read_html(uri))[0]

    # Create month dataframe
    month_data = pd.DataFrame()

    # Convert month calendar to transposed dataframe
    for i in list(range(len(month))):
        data = month[i:(i+1)].T
        data.columns = ['day']
        month_data = pd.concat([month_data, data])

    # Remove days from other months
    month_data = month_data[start:(-1*stop)]

    # Add month to data
    month_data['month'] = name
    month_data = month_data[['month', 'day']]

    # Seperate day from event
    month_data = month_data.astype(str)
    month_data['event'] = month_data.day.str[2:]
    month_data['day'] = month_data.day.str[:2]

    # Splits events with multiple events into two parts
    month_data['event'] = (month_data['event'].str.
                           replace("Birding Banshee ",
                                   "Birding Banshee | "))
    month_data['event'] = (month_data['event'].str.
                           replace("Birding Bles Park ",
                                   "Birding Bles Park | "))

    return month_data


def concat_calendars(months):
    """
    Runs 'event_calendar' function for each month listed and
    concats the results.

    Parameters:
    months: List of dictionaries for each month containing
            the parameters for the 'event_calendar' function.

    Returns:
    calendar_df: Dataframe combining the calendars for each month listed.
    """

    # Create 'calendar' dataframe
    calendar_df = pd.DataFrame()

    # Add results from each month to dataframe
    for month in months:
        data = event_calendar(uri=month['uri'], name=month['name'],
                              start=month['start'], stop=month['stop'])
        calendar_df = pd.concat([calendar_df, data])

    return calendar_df


def calendar():
    """Creates calendar for Dec 2019 - Feb 2020."""

    dec = {'uri': 'https://loudounwildlife.org/events/',
           'name': 'Dec', 'start': 6, 'stop': 5}
    jan = {'uri': 'https://loudounwildlife.org/events/2020-01/',
           'name': 'Jan', 'start': 2, 'stop': 2}
    feb = {'uri': 'https://loudounwildlife.org/events/2020-02/',
           'name': 'Feb', 'start': 5, 'stop': 1}
    months = [dec, jan, feb]
    calendar_df = concat_calendars(months)
    return calendar_df
