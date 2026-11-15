"""NASA variable catalogue used by the explorer and methodology views."""

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Variable:
    code: str
    name: str
    definition: str
    unit: str
    aggregation: str
    source: str
    coverage: str
    resolution: str
    limitations: str

    def as_dict(self):
        return asdict(self)


VARIABLES = {
    "T2M": Variable(
        "T2M", "Air temperature at 2 m", "Mean air temperature at 2 metres above the surface.",
        "°C", "annual mean", "NASA POWER / MERRA-2", "1981–present", "0.5° × 0.625°", 
        "Reanalysis-derived estimate; representative point, not a station observation.",
    ),
    "T2M_MAX": Variable(
        "T2M_MAX", "Daily maximum air temperature", "Mean daily maximum air temperature at 2 metres.",
        "°C", "annual mean", "NASA POWER / MERRA-2", "1981–present", "0.5° × 0.625°",
        "Reanalysis-derived estimate; extremes are summarized as daily means.",
    ),
    "T2M_MIN": Variable(
        "T2M_MIN", "Daily minimum air temperature", "Mean daily minimum air temperature at 2 metres.",
        "°C", "annual mean", "NASA POWER / MERRA-2", "1981–present", "0.5° × 0.625°",
        "Reanalysis-derived estimate; extremes are summarized as daily means.",
    ),
    "PRECTOTCORR": Variable(
        "PRECTOTCORR", "Corrected precipitation", "Bias-corrected total precipitation at the surface.",
        "mm/day", "annual total", "NASA POWER / MERRA-2", "1981–present", "0.5° × 0.625°",
        "Model-derived precipitation estimate; annual aggregation sums valid daily values.",
    ),
    "RH2M": Variable(
        "RH2M", "Relative humidity at 2 m", "Relative humidity at 2 metres above the surface.",
        "%", "annual mean", "NASA POWER / MERRA-2", "1981–present", "0.5° × 0.625°",
        "Reanalysis-derived estimate; humidity can be sensitive to local elevation mismatch.",
    ),
    "WS10M": Variable(
        "WS10M", "Wind speed at 10 m", "Wind speed at 10 metres above the surface.",
        "m/s", "annual mean", "NASA POWER / MERRA-2", "1981–present", "0.5° × 0.625°",
        "Reanalysis-derived estimate; topography and land-cover effects are smoothed.",
    ),
}


def get_variable(code: str) -> Variable:
    return VARIABLES[code]

