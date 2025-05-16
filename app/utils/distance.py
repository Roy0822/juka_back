import math
from typing import Tuple

def calculate_distance(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float, 
    unit: str = 'km'
) -> float:
    """
    Calculate distance between two geographical points
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        unit: Unit of result ('km' or 'm')
        
    Returns:
        Distance in specified unit
    """
    # Earth radius in kilometers
    earth_radius = 6371.0
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = earth_radius * c
    
    # Convert to meters if requested
    if unit == 'm':
        distance = distance * 1000
        
    return distance

def get_bounding_box(
    latitude: float, 
    longitude: float, 
    distance_km: float
) -> Tuple[float, float, float, float]:
    """
    Get a rough bounding box for a distance around a point
    Useful for preliminary filtering before precise distance calculation
    
    Args:
        latitude: Center point latitude
        longitude: Center point longitude
        distance_km: Distance in kilometers
        
    Returns:
        Tuple of (min_lat, min_lon, max_lat, max_lon)
    """
    # Earth's radius, sphere
    earth_radius = 6371.0
    
    # Coordinate offsets in radians
    lat_rad = math.radians(latitude)
    
    # Radius of a parallel at given latitude
    parallel_radius = earth_radius * math.cos(lat_rad)
    
    # Angular distance in radians on a great circle
    angular_distance = distance_km / earth_radius
    
    # Horizontal angular distance
    horizontal_distance = distance_km / parallel_radius if parallel_radius > 0 else 0
    
    min_lat = latitude - math.degrees(angular_distance)
    max_lat = latitude + math.degrees(angular_distance)
    
    min_lon = longitude - math.degrees(horizontal_distance)
    max_lon = longitude + math.degrees(horizontal_distance)
    
    return (min_lat, min_lon, max_lat, max_lon) 