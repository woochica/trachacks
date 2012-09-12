# -*- coding: utf-8 -*-

def total_hours(feed):
    """return a dictionary in the form of {worker: hours_worked}"""
    hours_dict = {}

    for entry in feed.entries:
        # the feed titles are formulated to permit easy extraction of hours
        title = entry.title
        split = title.split()
        hours, minutes = split[0].split(':')
        time_worked = float(hours) + float(minutes)/60. # in hours
        worker = split[-1]
        hours_dict.setdefault(worker, 0)
        hours_dict[worker] += time_worked
    return hours_dict

        
