"""Utility functions for GrowFlow."""
import math


def calculate_vpd(temperature: float, humidity: float) -> float:
    """
    Calculate Vapor Pressure Deficit (VPD) in kPa.
    
    VPD = SVP * (1 - RH/100)
    
    Where:
    - SVP = Saturated Vapor Pressure
    - RH = Relative Humidity
    """
    # Saturated Vapor Pressure berechnen (Magnus-Formel)
    svp = 0.6108 * math.exp((17.27 * temperature) / (temperature + 237.3))
    
    # VPD berechnen
    vpd = svp * (1 - humidity / 100)
    
    return round(vpd, 2)


def get_vpd_status(vpd: float) -> str:
    """Get VPD status description."""
    if vpd < 0.5:
        return "Too Low"
    elif vpd > 1.5:
        return "Too High"
    elif 0.8 <= vpd <= 1.2:
        return "Optimal"
    else:
        return "Good"


def calculate_target_humidity(temperature: float, target_vpd: float) -> float:
    """
    Calculate target humidity based on temperature and target VPD.
    
    VPD = SVP * (1 - RH/100)
    => RH = (1 - VPD/SVP) * 100
    """
    # Saturated Vapor Pressure berechnen
    svp = 0.6108 * math.exp((17.27 * temperature) / (temperature + 237.3))
    
    # Ziel-Feuchtigkeit berechnen
    target_humidity = (1 - target_vpd / svp) * 100
    
    # Auf sinnvolle Werte begrenzen
    target_humidity = max(30, min(90, target_humidity))
    
    return round(target_humidity, 1)


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9/5) + 32