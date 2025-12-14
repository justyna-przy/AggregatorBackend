"""
Analytics module for elevator data aggregation and statistics.
Provides functions to query and analyze elevator events from the database.
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_
from models import db, Event, EventType


# Trip Statistics

def get_total_trips(start_date=None, end_date=None):
    """
    Count total number of trips (destination button presses).
    A trip represents someone actually using the elevator to travel.
    Only counts inside destination buttons, not call buttons.
    
    Args:
        start_date: Optional datetime to filter from
        end_date: Optional datetime to filter to
        
    Returns:
        int: Total number of trips
    """
    query = db.session.query(func.count(Event.id)).join(EventType).filter(
        EventType.event_type.in_([
            'button_inside_0',
            'button_inside_1',
            'button_inside_2'
        ])
    )
    
    if start_date:
        query = query.filter(Event.timestamp >= start_date)
    if end_date:
        query = query.filter(Event.timestamp <= end_date)
    
    return query.scalar() or 0


def get_total_floor_passes(start_date=None, end_date=None):
    """
    Count how many times the elevator passed through each floor level.
    This includes both stops and pass-throughs.
    
    Args:
        start_date: Optional datetime to filter from
        end_date: Optional datetime to filter to
        
    Returns:
        int: Total number of floor passes
    """
    query = db.session.query(func.count(Event.id)).join(EventType).filter(
        EventType.event_type.in_([
            'floor_reached_0',
            'floor_reached_1',
            'floor_reached_2'
        ])
    )
    
    if start_date:
        query = query.filter(Event.timestamp >= start_date)
    if end_date:
        query = query.filter(Event.timestamp <= end_date)
    
    return query.scalar() or 0


def get_trips_by_floor(start_date=None, end_date=None):
    """
    Count trips to each floor (destination button presses by floor).
    
    Args:
        start_date: Optional datetime to filter from
        end_date: Optional datetime to filter to
        
    Returns:
        dict: {floor_number: trip_count}
    """
    query = db.session.query(
        Event.floor,
        func.count(Event.id).label('count')
    ).join(EventType).filter(
        EventType.event_type.in_([
            'button_inside_0',
            'button_inside_1',
            'button_inside_2'
        ])
    ).group_by(Event.floor)
    
    if start_date:
        query = query.filter(Event.timestamp >= start_date)
    if end_date:
        query = query.filter(Event.timestamp <= end_date)
    
    results = query.all()
    return {floor: count for floor, count in results}


def get_floor_passes_by_floor(start_date=None, end_date=None):
    """
    Count how many times the elevator passed through each floor.
    Includes both stops and pass-throughs.
    
    Args:
        start_date: Optional datetime to filter from
        end_date: Optional datetime to filter to
        
    Returns:
        dict: {floor_number: pass_count}
    """
    query = db.session.query(
        Event.floor,
        func.count(Event.id).label('count')
    ).join(EventType).filter(
        EventType.event_type.in_([
            'floor_reached_0',
            'floor_reached_1',
            'floor_reached_2'
        ])
    ).group_by(Event.floor)
    
    if start_date:
        query = query.filter(Event.timestamp >= start_date)
    if end_date:
        query = query.filter(Event.timestamp <= end_date)
    
    results = query.all()
    return {floor: count for floor, count in results}


# Button Press Statistics

def get_button_press_counts(start_date=None, end_date=None):
    """
    Count button presses by type (inside buttons vs call buttons).
    
    Args:
        start_date: Optional datetime to filter from
        end_date: Optional datetime to filter to
        
    Returns:
        dict: {
            'inside_buttons': count,
            'call_buttons': count,
            'total': count
        }
    """
    inside_buttons = [
        'button_inside_0',
        'button_inside_1',
        'button_inside_2'
    ]
    
    call_buttons = [
        'call_button_0_up',
        'call_button_1_up',
        'call_button_1_down',
        'call_button_2_down'
    ]
    
    # Query inside buttons
    inside_query = db.session.query(func.count(Event.id)).join(EventType).filter(
        EventType.event_type.in_(inside_buttons)
    )
    if start_date:
        inside_query = inside_query.filter(Event.timestamp >= start_date)
    if end_date:
        inside_query = inside_query.filter(Event.timestamp <= end_date)
    
    # Query call buttons
    call_query = db.session.query(func.count(Event.id)).join(EventType).filter(
        EventType.event_type.in_(call_buttons)
    )
    if start_date:
        call_query = call_query.filter(Event.timestamp >= start_date)
    if end_date:
        call_query = call_query.filter(Event.timestamp <= end_date)
    
    inside_count = inside_query.scalar() or 0
    call_count = call_query.scalar() or 0
    
    return {
        'inside_buttons': inside_count,
        'call_buttons': call_count,
        'total': inside_count + call_count
    }


def get_most_requested_floor(start_date=None, end_date=None):
    """
    Find which floor is requested most often (both inside and call buttons).
    
    Args:
        start_date: Optional datetime to filter from
        end_date: Optional datetime to filter to
        
    Returns:
        dict: {'floor': floor_number, 'count': request_count}
    """
    button_events = [
        'button_inside_0', 'button_inside_1', 'button_inside_2',
        'call_button_0_up', 'call_button_1_up',
        'call_button_1_down', 'call_button_2_down'
    ]
    
    query = db.session.query(
        Event.floor,
        func.count(Event.id).label('count')
    ).join(EventType).filter(
        EventType.event_type.in_(button_events),
        Event.floor.isnot(None)
    ).group_by(Event.floor).order_by(func.count(Event.id).desc())
    
    if start_date:
        query = query.filter(Event.timestamp >= start_date)
    if end_date:
        query = query.filter(Event.timestamp <= end_date)
    
    result = query.first()
    if result:
        return {'floor': result.floor, 'count': result.count}
    return {'floor': None, 'count': 0}


# Emergency Events

def get_emergency_stop_count(start_date=None, end_date=None):
    """
    Count how many times emergency stop was activated.
    
    Args:
        start_date: Optional datetime to filter from
        end_date: Optional datetime to filter to
        
    Returns:
        int: Number of emergency stop activations
    """
    query = db.session.query(func.count(Event.id)).join(EventType).filter(
        EventType.event_type == 'emergency_stop'
    )
    
    if start_date:
        query = query.filter(Event.timestamp >= start_date)
    if end_date:
        query = query.filter(Event.timestamp <= end_date)
    
    return query.scalar() or 0


def get_average_emergency_duration(start_date=None, end_date=None):
    """
    Calculate average time between emergency stop and release.
    
    Args:
        start_date: Optional datetime to filter from
        end_date: Optional datetime to filter to
        
    Returns:
        float: Average duration in seconds, or None if no data
    """
    # Get all emergency stop events
    stop_query = db.session.query(Event.timestamp).join(EventType).filter(
        EventType.event_type == 'emergency_stop'
    )
    if start_date:
        stop_query = stop_query.filter(Event.timestamp >= start_date)
    if end_date:
        stop_query = stop_query.filter(Event.timestamp <= end_date)
    
    stops = stop_query.order_by(Event.timestamp).all()
    
    # Get all emergency release events
    release_query = db.session.query(Event.timestamp).join(EventType).filter(
        EventType.event_type == 'emergency_released'
    )
    if start_date:
        release_query = release_query.filter(Event.timestamp >= start_date)
    if end_date:
        release_query = release_query.filter(Event.timestamp <= end_date)
    
    releases = release_query.order_by(Event.timestamp).all()
    
    if not stops or not releases:
        return None
    
    # Pair stops with their following releases
    durations = []
    for stop in stops:
        # Find next release after this stop
        for release in releases:
            if release.timestamp > stop.timestamp:
                duration = (release.timestamp - stop.timestamp).total_seconds()
                durations.append(duration)
                break
    
    if not durations:
        return None
    
    return sum(durations) / len(durations)


# Time-based Analytics

def get_events_by_hour(start_date=None, end_date=None):
    """
    Get event counts grouped by hour of day.
    
    Args:
        start_date: Optional datetime to filter from
        end_date: Optional datetime to filter to
        
    Returns:
        dict: {hour (0-23): event_count}
    """
    query = db.session.query(
        func.extract('hour', Event.timestamp).label('hour'),
        func.count(Event.id).label('count')
    )
    
    if start_date:
        query = query.filter(Event.timestamp >= start_date)
    if end_date:
        query = query.filter(Event.timestamp <= end_date)
    
    query = query.group_by('hour').order_by('hour')
    
    results = query.all()
    return {int(hour): count for hour, count in results}


def get_busiest_hour(start_date=None, end_date=None):
    """
    Find the hour with most elevator activity.
    
    Args:
        start_date: Optional datetime to filter from
        end_date: Optional datetime to filter to
        
    Returns:
        dict: {'hour': hour (0-23), 'event_count': count}
    """
    events_by_hour = get_events_by_hour(start_date, end_date)
    
    if not events_by_hour:
        return {'hour': None, 'event_count': 0}
    
    busiest = max(events_by_hour.items(), key=lambda x: x[1])
    return {'hour': busiest[0], 'event_count': busiest[1]}


def get_trips_per_day(days=7):
    """
    Get daily trip counts for the last N days.
    Counts destination button presses (actual trips).
    
    Args:
        days: Number of days to look back
        
    Returns:
        list: [{'date': 'YYYY-MM-DD', 'trips': count}, ...]
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    query = db.session.query(
        func.date(Event.timestamp).label('date'),
        func.count(Event.id).label('count')
    ).join(EventType).filter(
        EventType.event_type.in_([
            'button_inside_0',
            'button_inside_1',
            'button_inside_2'
        ]),
        Event.timestamp >= start_date
    ).group_by('date').order_by('date')
    
    results = query.all()
    return [{'date': str(date), 'trips': count} for date, count in results]


# Connection Health

def get_connection_stats(start_date=None, end_date=None):
    """
    Get statistics about Maxim connection health.
    
    Args:
        start_date: Optional datetime to filter from
        end_date: Optional datetime to filter to
        
    Returns:
        dict: {
            'connections': count,
            'disconnections': count,
            'connection_rate': percentage
        }
    """
    # Count connections
    conn_query = db.session.query(func.count(Event.id)).join(EventType).filter(
        EventType.event_type == 'maxim_connected'
    )
    if start_date:
        conn_query = conn_query.filter(Event.timestamp >= start_date)
    if end_date:
        conn_query = conn_query.filter(Event.timestamp <= end_date)
    
    connections = conn_query.scalar() or 0
    
    # Count disconnections
    disconn_query = db.session.query(func.count(Event.id)).join(EventType).filter(
        EventType.event_type == 'maxim_connection_lost'
    )
    if start_date:
        disconn_query = disconn_query.filter(Event.timestamp >= start_date)
    if end_date:
        disconn_query = disconn_query.filter(Event.timestamp <= end_date)
    
    disconnections = disconn_query.scalar() or 0
    
    total = connections + disconnections
    connection_rate = (connections / total * 100) if total > 0 else 0
    
    return {
        'connections': connections,
        'disconnections': disconnections,
        'connection_rate': round(connection_rate, 2)
    }


# Comprehensive Summary

def get_summary_stats(start_date=None, end_date=None):
    """
    Get a comprehensive summary of all elevator statistics.
    
    Args:
        start_date: Optional datetime to filter from
        end_date: Optional datetime to filter to
        
    Returns:
        dict: Comprehensive statistics dictionary
    """
    return {
        'trips': {
            'total': get_total_trips(start_date, end_date),
            'by_floor': get_trips_by_floor(start_date, end_date)
        },
        'buttons': get_button_press_counts(start_date, end_date),
        'most_requested_floor': get_most_requested_floor(start_date, end_date),
        'emergency': {
            'activations': get_emergency_stop_count(start_date, end_date),
            'avg_duration_seconds': get_average_emergency_duration(start_date, end_date)
        },
        'time_analysis': {
            'busiest_hour': get_busiest_hour(start_date, end_date),
            'events_by_hour': get_events_by_hour(start_date, end_date)
        },
        'connection_health': get_connection_stats(start_date, end_date)
    }
